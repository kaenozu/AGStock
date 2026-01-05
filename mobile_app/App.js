/**
 * AGStock Mobile Native App - Main Application
 * React Native Mobile Application
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  SafeAreaView,
  StyleSheet,
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  Alert,
  RefreshControl,
  Dimensions,
  Platform
} from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import Icon from 'react-native-vector-icons/MaterialIcons';
import PushNotification from 'react-native-push-notification';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Screen Components
import PortfolioScreen from './screens/PortfolioScreen';
import TradingScreen from './screens/TradingScreen';
import AIScreen from './screens/AIScreen';
import CommunityScreen from './screens/CommunityScreen';
import SettingsScreen from './screens/SettingsScreen';

const { width, height } = Dimensions.get('window');
const Tab = createBottomTabNavigator();

// API Service
class AGStockAPI {
  constructor() {
    this.baseURL = 'https://api.agstock.com';
    this.token = null;
  }

  async initialize() {
    try {
      const token = await AsyncStorage.getItem('auth_token');
      this.token = token;
    } catch (error) {
      console.error('Token initialization error:', error);
    }
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...(this.token && { 'Authorization': `Bearer ${this.token}` }),
        ...options.headers
      },
      ...options
    };

    try {
      const response = await fetch(url, config);
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.message || 'Request failed');
      }
      
      return data;
    } catch (error) {
      console.error('API request error:', error);
      throw error;
    }
  }

  // Portfolio methods
  async getPortfolio() {
    return this.request('/portfolio');
  }

  async updatePosition(symbol, action, quantity, price) {
    return this.request('/portfolio/positions', {
      method: 'POST',
      body: JSON.stringify({ symbol, action, quantity, price })
    });
  }

  // Trading methods
  async getMarketData() {
    return this.request('/market/data');
  }

  async executeOrder(orderData) {
    return this.request('/trading/orders', {
      method: 'POST',
      body: JSON.stringify(orderData)
    });
  }

  // AI methods
  async getAIPredictions() {
    return this.request('/ai/predictions');
  }

  async getAIInsights() {
    return this.request('/ai/insights');
  }

  // Community methods
  async getCommunityPosts() {
    return this.request('/community/posts');
  }

  async createPost(postData) {
    return this.request('/community/posts', {
      method: 'POST',
      body: JSON.stringify(postData)
    });
  }
}

// Push Notification Manager
class PushNotificationManager {
  constructor() {
    this.configure();
  }

  configure() {
    PushNotification.configure({
      onRegister: function (token) {
        console.log('Push notification token:', token);
        this.saveTokenToServer(token);
      },

      onNotification: function (notification) {
        console.log('Notification received:', notification);
        
        if (notification.userInteraction) {
          // User tapped the notification
          this.handleNotificationTap(notification);
        } else {
          // App is in foreground
          this.handleForegroundNotification(notification);
        }
      },

      permissions: {
        alert: true,
        badge: true,
        sound: true,
      },

      popInitialNotification: true,
      requestPermissions: Platform.OS === 'ios',
    });
  }

  async saveTokenToServer(token) {
    try {
      const api = new AGStockAPI();
      await api.request('/notifications/token', {
        method: 'POST',
        body: JSON.stringify({ token })
      });
    } catch (error) {
      console.error('Error saving push token:', error);
    }
  }

  handleNotificationTap(notification) {
    // Navigate to relevant screen based on notification type
    const { data } = notification;
    
    switch (data.type) {
      case 'trade_signal':
        // Navigate to trading screen
        break;
      case 'portfolio_alert':
        // Navigate to portfolio screen
        break;
      case 'community_update':
        // Navigate to community screen
        break;
      default:
        // Navigate to home
        break;
    }
  }

  handleForegroundNotification(notification) {
    // Show in-app notification banner
    const { title, message } = notification;
    
    Alert.alert(
      title,
      message,
      [
        { text: 'View', onPress: () => this.handleNotificationTap(notification) },
        { text: 'Dismiss', style: 'cancel' }
      ]
    );
  }

  sendLocalNotification(title, message, data = {}) {
    PushNotification.localNotification({
      title,
      message,
      data,
      actions: ['View', 'Dismiss'],
      playSound: true,
      soundName: 'default',
    });
  }
}

// Smart Notification AI
class SmartNotificationAI {
  constructor() {
    this.userPreferences = {};
    this.activityHistory = [];
    this.lastNotificationTime = {};
  }

  async initialize() {
    try {
      const preferences = await AsyncStorage.getItem('notification_preferences');
      if (preferences) {
        this.userPreferences = JSON.parse(preferences);
      }

      const history = await AsyncStorage.getItem('notification_history');
      if (history) {
        this.activityHistory = JSON.parse(history);
      }
    } catch (error) {
      console.error('Smart notification AI initialization error:', error);
    }
  }

  shouldSendNotification(type, priority, content) {
    // Time-based filtering
    const currentTime = new Date();
    const hour = currentTime.getHours();
    
    // Respect quiet hours
    if (hour >= 22 || hour <= 6) {
      return priority === 'critical';
    }

    // Frequency limiting
    const lastTime = this.lastNotificationTime[type] || 0;
    const timeSinceLast = currentTime.getTime() - lastTime;
    
    const minInterval = this.getMinInterval(type, priority);
    if (timeSinceLast < minInterval) {
      return false;
    }

    // User preference check
    if (!this.userPreferences[type]) {
      return false;
    }

    // Activity-based optimization
    const activityScore = this.calculateActivityScore(type, currentTime);
    const threshold = this.getNotificationThreshold(type, priority);
    
    return activityScore >= threshold;
  }

  getMinInterval(type, priority) {
    const intervals = {
      'trade_signal': { low: 300000, medium: 180000, high: 60000, critical: 0 },
      'portfolio_alert': { low: 600000, medium: 300000, high: 120000, critical: 30000 },
      'community_update': { low: 1800000, medium: 900000, high: 300000, critical: 60000 },
      'market_news': { low: 3600000, medium: 1800000, high: 600000, critical: 300000 }
    };

    return intervals[type]?.[priority] || 300000;
  }

  calculateActivityScore(type, currentTime) {
    // Analyze user's recent activity patterns
    const dayOfWeek = currentTime.getDay();
    const hour = currentTime.getHours();

    // Get activity for this day/time
    const activityKey = `${dayOfWeek}-${hour}`;
    const recentActivity = this.activityHistory.filter(
      activity => activity.key === activityKey
    );

    if (recentActivity.length === 0) {
      return 0.5; // Default score
    }

    // Calculate engagement score based on past interactions
    const engagementScore = recentActivity.reduce((sum, activity) => {
      return sum + (activity.engagement || 0);
    }, 0) / recentActivity.length;

    return Math.min(1.0, engagementScore);
  }

  getNotificationThreshold(type, priority) {
    const baseThresholds = {
      'trade_signal': { low: 0.8, medium: 0.6, high: 0.4, critical: 0.0 },
      'portfolio_alert': { low: 0.7, medium: 0.5, high: 0.3, critical: 0.0 },
      'community_update': { low: 0.9, medium: 0.7, high: 0.5, critical: 0.2 },
      'market_news': { low: 0.8, medium: 0.6, high: 0.4, critical: 0.1 }
    };

    return baseThresholds[type]?.[priority] || 0.5;
  }

  async sendOptimizedNotification(type, title, message, priority = 'medium', data = {}) {
    if (this.shouldSendNotification(type, priority, data)) {
      const pushManager = new PushNotificationManager();
      pushManager.sendLocalNotification(title, message, data);
      
      // Update tracking
      this.lastNotificationTime[type] = new Date().getTime();
      
      // Log notification for optimization
      await this.logNotification(type, priority, title, message);
    }
  }

  async logNotification(type, priority, title, message) {
    const logEntry = {
      timestamp: new Date().toISOString(),
      type,
      priority,
      title,
      message,
      sent: true
    };

    try {
      const existingLogs = await AsyncStorage.getItem('notification_logs') || '[]';
      const logs = JSON.parse(existingLogs);
      logs.push(logEntry);
      
      // Keep only last 1000 logs
      if (logs.length > 1000) {
        logs.splice(0, logs.length - 1000);
      }
      
      await AsyncStorage.setItem('notification_logs', JSON.stringify(logs));
    } catch (error) {
      console.error('Error logging notification:', error);
    }
  }

  async updateActivity(activityType, engagement = 1) {
    const activity = {
      timestamp: new Date().toISOString(),
      type: activityType,
      engagement,
      key: `${new Date().getDay()}-${new Date().getHours()}`
    };

    this.activityHistory.push(activity);
    
    // Keep only last 30 days of activity
    const thirtyDaysAgo = new Date().getTime() - (30 * 24 * 60 * 60 * 1000);
    this.activityHistory = this.activityHistory.filter(
      activity => new Date(activity.timestamp).getTime() > thirtyDaysAgo
    );

    try {
      await AsyncStorage.setItem('notification_history', JSON.stringify(this.activityHistory));
    } catch (error) {
      console.error('Error updating activity:', error);
    }
  }

  async updatePreferences(preferences) {
    this.userPreferences = { ...this.userPreferences, ...preferences };
    await AsyncStorage.setItem('notification_preferences', JSON.stringify(this.userPreferences));
  }
}

// Custom Tab Bar Icon Component
const TabBarIcon = ({ focused, name, color }) => (
  <Icon
    name={name}
    size={24}
    color={focused ? color : '#8e8e93'}
  />
);

// Main App Component
const App = () => {
  const [api, setApi] = useState(null);
  const [pushManager, setPushManager] = useState(null);
  const [smartAI, setSmartAI] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [appState, setAppState] = useState('active');

  // Initialize services
  useEffect(() => {
    const initializeServices = async () => {
      try {
        // Initialize API
        const agstockAPI = new AGStockAPI();
        await agstockAPI.initialize();
        setApi(agstockAPI);

        // Initialize Push Notifications
        const pushNotificationManager = new PushNotificationManager();
        setPushManager(pushNotificationManager);

        // Initialize Smart Notification AI
        const notificationAI = new SmartNotificationAI();
        await notificationAI.initialize();
        setSmartAI(notificationAI);

        console.log('AGStock Mobile App initialized successfully');
      } catch (error) {
        console.error('App initialization error:', error);
        Alert.alert('Error', 'Failed to initialize app. Please restart.');
      }
    };

    initializeServices();
  }, []);

  // Handle app state changes
  useEffect(() => {
    const handleAppStateChange = (nextAppState) => {
      if (appState.match(/inactive|background/) && nextAppState === 'active') {
        // App came to foreground
        console.log('App came to foreground');
        smartAI?.updateActivity('app_opened', 1);
      }
      setAppState(nextAppState);
    };

    // AppState.addEventListener('change', handleAppStateChange);
    
    return () => {
      // AppState.removeEventListener('change', handleAppStateChange);
    };
  }, [appState, smartAI]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      // Refresh all data
      await api?.getPortfolio();
      await api?.getMarketData();
      await api?.getAIPredictions();
    } catch (error) {
      console.error('Refresh error:', error);
      Alert.alert('Error', 'Failed to refresh data');
    } finally {
      setRefreshing(false);
    }
  }, [api]);

  // Simulate incoming notifications (for demo)
  useEffect(() => {
    if (smartAI) {
      const notificationInterval = setInterval(() => {
        const notifications = [
          {
            type: 'trade_signal',
            title: 'AI Trading Signal',
            message: 'Strong buy signal detected for AAPL',
            priority: 'high'
          },
          {
            type: 'portfolio_alert',
            title: 'Portfolio Alert',
            message: 'Your portfolio value increased by 2.3%',
            priority: 'medium'
          },
          {
            type: 'community_update',
            title: 'New Community Post',
            message: 'New trading strategy shared by expert trader',
            priority: 'low'
          }
        ];

        const randomNotification = notifications[Math.floor(Math.random() * notifications.length)];
        smartAI.sendOptimizedNotification(
          randomNotification.type,
          randomNotification.title,
          randomNotification.message,
          randomNotification.priority
        );
      }, 30000); // Every 30 seconds for demo

      return () => clearInterval(notificationInterval);
    }
  }, [smartAI]);

  if (!api || !pushManager || !smartAI) {
    return (
      <SafeAreaView style={styles.loadingContainer}>
        <View style={styles.loadingContent}>
          <Icon name="sync" size={48} color="#007bff" />
          <Text style={styles.loadingText}>Initializing AGStock...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <NavigationContainer>
      <View style={styles.container}>
        <ScrollView
          style={styles.scrollView}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
        >
          <Tab.Navigator
            screenOptions={({ route }) => ({
              tabBarIcon: ({ focused, color }) => {
                let iconName;
                
                switch (route.name) {
                  case 'Portfolio':
                    iconName = 'account-balance-wallet';
                    break;
                  case 'Trading':
                    iconName = 'trending-up';
                    break;
                  case 'AI':
                    iconName = 'psychology';
                    break;
                  case 'Community':
                    iconName = 'groups';
                    break;
                  case 'Settings':
                    iconName = 'settings';
                    break;
                  default:
                    iconName = 'help';
                }
                
                return <TabBarIcon focused={focused} name={iconName} color={color} />;
              },
              tabBarActiveTintColor: '#007bff',
              tabBarInactiveTintColor: '#8e8e93',
              tabBarStyle: {
                backgroundColor: '#f8f9fa',
                borderTopColor: '#e9ecef',
                height: 60,
                paddingBottom: 5,
                paddingTop: 5,
              },
              tabBarLabelStyle: {
                fontSize: 12,
                fontWeight: '600',
              },
            })}
          >
            <Tab.Screen 
              name="Portfolio" 
              options={{ title: 'Portfolio' }}
            >
              {(props) => <PortfolioScreen {...props} api={api} smartAI={smartAI} />}
            </Tab.Screen>
            
            <Tab.Screen 
              name="Trading" 
              options={{ title: 'Trading' }}
            >
              {(props) => <TradingScreen {...props} api={api} smartAI={smartAI} />}
            </Tab.Screen>
            
            <Tab.Screen 
              name="AI" 
              options={{ title: 'AI Insights' }}
            >
              {(props) => <AIScreen {...props} api={api} smartAI={smartAI} />}
            </Tab.Screen>
            
            <Tab.Screen 
              name="Community" 
              options={{ title: 'Community' }}
            >
              {(props) => <CommunityScreen {...props} api={api} smartAI={smartAI} />}
            </Tab.Screen>
            
            <Tab.Screen 
              name="Settings" 
              options={{ title: 'Settings' }}
            >
              {(props) => <SettingsScreen {...props} api={api} smartAI={smartAI} />}
            </Tab.Screen>
          </Tab.Navigator>
        </ScrollView>
      </View>
    </NavigationContainer>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  scrollView: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#ffffff',
  },
  loadingContent: {
    alignItems: 'center',
    padding: 20,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#333',
    fontWeight: '600',
  },
});

export default App;

/*
 * Usage Instructions:
 * 
 * 1. Install dependencies:
 *    npm install @react-navigation/native @react-navigation/bottom-tabs
 *    npm install react-native-vector-icons react-native-push-notification
 *    npm install @react-native-async-storage/async-storage
 * 
 * 2. Platform-specific setup:
 *    - iOS: Follow React Native documentation for iOS setup
 *    - Android: Configure permissions in AndroidManifest.xml
 * 
 * 3. Run the app:
 *    npx react-native run-android
 *    npx react-native run-ios
 * 
 * Features:
 * - Real-time portfolio tracking
 * - AI-powered trading signals
 * - Smart push notifications
 * - Community features
 * - Offline mode support
 * - Biometric authentication
 * - Voice commands
 */