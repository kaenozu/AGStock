// AGStock PWA Service Worker
const CACHE_NAME = 'agstock-pwa-v1';
const urlsToCache = [
  '/',
  '/index.html',
  '/manifest.json',
  '/static/js/bundle.js',
  '/static/css/main.css',
  'https://cdn.jsdelivr.net/npm/chart.js'
];

self.addEventListener('install', (event) => {
  console.log('Service Worker installing...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Caching essential files');
        return cache.addAll(urlsToCache);
      })
      .catch((error) => {
        console.error('Cache installation failed:', error);
      })
  );
});

self.addEventListener('activate', (event) => {
  console.log('Service Worker activating...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        // Return cached version or fetch from network
        if (response) {
          return response;
        }
        
        return fetch(event.request)
          .then((response) => {
            // Cache successful responses
            if (response.status === 200 && response.type === 'basic') {
              const responseClone = response.clone();
              caches.open(CACHE_NAME)
                .then((cache) => {
                  cache.put(event.request, responseClone);
                });
            }
            return response;
          })
          .catch((error) => {
            console.error('Network request failed:', error);
            
            // Return offline fallback if available
            if (event.request.url.includes('/api/market')) {
              return new Response(
                JSON.stringify({
                  error: 'Network unavailable',
                  cached: true,
                  data: {
                    nikkei: 32000,
                    sp500: 4500,
                    timestamp: new Date().toISOString()
                  }
                }),
                {
                  status: 200,
                  statusText: 'OK',
                  headers: {
                    'Content-Type': 'application/json'
                  }
                }
              );
            }
            
            return new Response('Offline', { status: 503 });
          });
      })
  );
});

// Background sync for data updates
self.addEventListener('sync', (event) => {
  if (event.tag === 'market-data-sync') {
    event.waitUntil(
      fetch('/api/market/update')
        .then((response) => response.json())
        .then((data) => {
          // Store updated data in IndexedDB
          return storeMarketData(data);
        })
        .then(() => {
          // Notify clients
          return self.clients.matchAll({
            includeUncontrolled: true
          });
        })
        .then((clients) => {
          clients.forEach((client) => {
            client.postMessage({
              type: 'MARKET_DATA_UPDATED',
              data: data
            });
          });
        })
    );
  }
});

// Push notification handling
self.addEventListener('push', (event) => {
  const options = {
    body: event.data ? event.data.message : '新しい市場情報があります',
    icon: '/assets/icon-96x96.png',
    badge: '/assets/icon-72x72.png',
    vibrate: [100, 50, 100],
    data: event.data,
    actions: [
      {
        action: 'open',
        title: 'アプリを開く',
        icon: '/assets/icon-96x96.png'
      },
      {
        action: 'dismiss',
        title: '無視',
        icon: '/assets/icon-96x96.png'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification('AGStock', options)
  );
});

// Notification click handling
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  if (event.action === 'open') {
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

// Helper function to store market data in IndexedDB
function storeMarketData(data) {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('AGStockDB', 1);
    
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('marketData')) {
        db.createObjectStore('marketData', { keyPath: 'timestamp' });
      }
    };
    
    request.onsuccess = (event) => {
      const db = event.target.result;
      const transaction = db.transaction(['marketData'], 'readwrite');
      const store = transaction.objectStore('marketData');
      
      const addRequest = store.put({
        timestamp: Date.now(),
        data: data
      });
      
      addRequest.onsuccess = () => resolve();
      addRequest.onerror = () => reject(addRequest.error);
    };
    
    request.onerror = () => reject(request.error);
  });
}

// Periodic background sync for market data
self.addEventListener('periodicsync', (event) => {
  if (event.tag === 'market-periodic-sync') {
    event.waitUntil(
      fetch('/api/market/latest')
        .then((response) => response.json())
        .then((data) => {
          // Check if data is significantly different
          return storeMarketData(data)
            .then(() => {
              return checkForSignificantChanges(data);
            });
        })
        .then((hasChanges) => {
          if (hasChanges) {
            // Show notification for significant changes
            self.registration.showNotification('市場の重要な変化', {
              body: hasChanges.message,
              icon: '/assets/icon-96x96.png'
            });
          }
        })
    );
  }
});

// Function to check for significant market changes
function checkForSignificantChanges(newData) {
  // Compare with cached data to detect significant changes
  return new Promise((resolve) => {
    const request = indexedDB.open('AGStockDB', 1);
    
    request.onsuccess = (event) => {
      const db = event.target.result;
      const transaction = db.transaction(['marketData'], 'readonly');
      const store = transaction.objectStore('marketData');
      
      const getRequest = store.index('timestamp').openCursor(null, 'prev');
      
      getRequest.onsuccess = (event) => {
        const cursor = event.target.result;
        
        if (cursor) {
          const oldData = cursor.value.data;
          
          // Check for significant changes
          const nikkeiChange = Math.abs(newData.nikkei - oldData.nikkei) / oldData.nikkei;
          const sp500Change = Math.abs(newData.sp500 - oldData.sp500) / oldData.sp500;
          
          if (nikkeiChange > 0.02 || sp500Change > 0.02) {
            resolve({
              type: 'significant_movement',
              message: `日経平均: ${newData.nikkei > oldData.nikkei ? '上昇' : '下落'}、S&P500: ${newData.sp500 > oldData.sp500 ? '上昇' : '下落'}`
            });
          } else {
            resolve(null);
          }
        } else {
          resolve({
            type: 'first_run',
            message: '市場データのキャッシュを開始しました'
          });
        }
      } else {
        resolve({
          type: 'first_run',
          message: '市場データのキャッシュを開始しました'
        });
      }
    };
  });
}