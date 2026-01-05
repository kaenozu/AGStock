"""
AGStock Personal Edition Mobile App
React Native モバイルアプリケーション
"""

import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Alert,
  Vibration,
} from 'react-native';
import { useState, useEffect } from 'react';
import Voice from '@react-native-voice/voice';
import PushNotification from 'react-native-push-notification';

// ワンタップ操作用コンポーネント
const QuickTradeButton = ({ symbol, action, onPress, price, change }) => {
  const color = action === 'BUY' ? '#4CAF50' : '#F44336';
  const bgColor = change >= 0 ? '#E8F5E8' : '#FFEBEE';
  
  return (
    <TouchableOpacity
      style={[styles.quickTradeButton, { backgroundColor: bgColor, borderColor: color }]}
      onPress={() => {
        Vibration.vibrate(100);
        Alert.alert(
          '確認',
          `${action} ${symbol} @ $${price}?`,
          [
            { text: 'キャンセル', style: 'cancel' },
            { text: '実行', onPress: () => onPress(symbol, action, price) }
          ]
        );
      }}
    >
      <Text style={[styles.quickTradeText, { color }]}>
        {action}
      </Text>
      <Text style={styles.symbolText}>{symbol}</Text>
      <Text style={styles.priceText}>${price}</Text>
      <Text style={[styles.changeText, { color: change >= 0 ? '#4CAF50' : '#F44336' }]}>
        {change >= 0 ? '+' : ''}{change.toFixed(2)}%
      </Text>
    </TouchableOpacity>
  );
};

// 音声制御用コンポーネント
const VoiceControl = ({ onCommand }) => {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');

  useEffect(() => {
    Voice.onSpeechStart = () => setIsListening(true);
    Voice.onSpeechEnd = () => setIsListening(false);
    Voice.onSpeechResults = (e) => {
      setTranscript(e.value[0]);
      processCommand(e.value[0]);
    };

    return () => {
      Voice.destroy().then(Voice.removeAllListeners);
    };
  }, []);

  const processCommand = (text) => {
    const command = text.toLowerCase();
    
    // 取引コマンド解析
    if (command.includes('買って') || command.includes('買い')) {
      const match = command.match(/(\w+)\s*(\d+)\s*株/);
      if (match) {
        onCommand('BUY', match[1].toUpperCase(), match[2]);
      }
    } else if (command.includes('売って') || command.includes('売り')) {
      const match = command.match(/(\w+)\s*(\d+)\s*株/);
      if (match) {
        onCommand('SELL', match[1].toUpperCase(), match[2]);
      }
    } else if (command.includes('状況') || command.includes('ステータス')) {
      onCommand('STATUS');
    } else if (command.includes('ニュース')) {
      onCommand('NEWS');
    }
  };

  const startListening = async () => {
    try {
      await Voice.start('ja-JP');
    } catch (e) {
      console.error(e);
    }
  };

  const stopListening = async () => {
    try {
      await Voice.stop();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <View style={styles.voiceControl}>
      <TouchableOpacity
        style={[styles.voiceButton, isListening && styles.voiceButtonActive]}
        onPress={isListening ? stopListening : startListening}
      >
        <Text style={styles.voiceButtonText}>
          {isListening ? '🛑' : '🎙️'}
        </Text>
      </TouchableOpacity>
      {transcript && (
        <Text style={styles.transcript}>{transcript}</Text>
      )}
    </View>
  );
};

// メインアプリ
const AGStockMobile = () => {
  const [portfolio, setPortfolio] = useState({});
  const [watchlist, setWatchlist] = useState([
    { symbol: 'AAPL', price: 175.50, change: 1.25 },
    { symbol: 'MSFT', price: 375.25, change: -0.50 },
    { symbol: 'GOOGL', price: 142.75, change: 0.75 },
  ]);
  const [notifications, setNotifications] = useState([]);

  // プッシュ通知初期化
  useEffect(() => {
    PushNotification.configure({
      onNotification: (notification) => {
        setNotifications(prev => [...prev, notification]);
      },
      permissions: {
        alert: true,
        badge: true,
        sound: true,
      },
    });

    PushNotification.createChannel(
      {
        channelId: 'agstock-trading',
        channelName: 'AGStock Trading',
        channelDescription: 'Trading notifications',
        importance: 4,
        vibrate: true,
      },
    );
  }, []);

  // ワンタップ取引処理
  const handleQuickTrade = (symbol, action, price) => {
    // 取引実行ロジック
    console.log(`Quick Trade: ${action} ${symbol} @ ${price}`);
    
    PushNotification.localNotification({
      channelId: 'agstock-trading',
      title: '取引実行',
      message: `${action} ${symbol} @ $${price}`,
      playSound: true,
      soundName: 'default',
    });
  };

  // 音声コマンド処理
  const handleVoiceCommand = (action, symbol, quantity) => {
    console.log(`Voice Command: ${action} ${symbol} ${quantity}`);
    Alert.alert('音声コマンド', `${action} ${symbol} ${quantity}株`);
  };

  // バッテリー最適化
  useEffect(() => {
    const updateInterval = 30000; // 30秒ごと
    const fetchData = () => {
      // データ取得ロジック（節電モード時は頻度を下げる）
    };

    const interval = setInterval(fetchData, updateInterval);
    return () => clearInterval(interval);
  }, []);

  return (
    <ScrollView style={styles.container}>
      {/* ヘッダー */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>AGStock Personal</Text>
        <View style={styles.headerStats}>
          <Text style={styles.portfolioValue}>$1,245,678</Text>
          <Text style={styles.portfolioChange}>+2.85% 今日</Text>
        </View>
      </View>

      {/* 音声制御 */}
      <VoiceControl onCommand={handleVoiceCommand} />

      {/* ワンタップ操作 */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>ワンタップ取引</Text>
        <View style={styles.quickTradeGrid}>
          {watchlist.map((stock, index) => (
            <QuickTradeButton
              key={index}
              symbol={stock.symbol}
              price={stock.price}
              change={stock.change}
              onPress={handleQuickTrade}
            />
          ))}
        </View>
      </View>

      {/* ポートフォリオ概要 */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>今日の動き</Text>
        <View style={styles.summaryCards}>
          <View style={[styles.summaryCard, { backgroundColor: '#E8F5E8' }]}>
            <Text style={styles.summaryCardTitle}>利益</Text>
            <Text style={styles.summaryCardValue}>+$34,567</Text>
          </View>
          <View style={[styles.summaryCard, { backgroundColor: '#FFF3E0' }]}>
            <Text style={styles.summaryCardTitle}>取引回数</Text>
            <Text style={styles.summaryCardValue}>5回</Text>
          </View>
          <View style={[styles.summaryCard, { backgroundColor: '#E3F2FD' }]}>
            <Text style={styles.summaryCardTitle}>勝率</Text>
            <Text style={styles.summaryCardValue}>80%</Text>
          </View>
        </View>
      </View>

      {/* 重要通知 */}
      {notifications.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>重要通知</Text>
          {notifications.slice(0, 3).map((notif, index) => (
            <View key={index} style={styles.notificationItem}>
              <Text style={styles.notificationTitle}>{notif.title}</Text>
              <Text style={styles.notificationMessage}>{notif.message}</Text>
            </View>
          ))}
        </View>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  header: {
    backgroundColor: '#2196F3',
    padding: 20,
    paddingTop: 40,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: 'white',
    textAlign: 'center',
  },
  headerStats: {
    alignItems: 'center',
    marginTop: 10,
  },
  portfolioValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: 'white',
  },
  portfolioChange: {
    fontSize: 16,
    color: '#81C784',
    marginTop: 5,
  },
  section: {
    margin: 15,
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 15,
    color: '#333',
  },
  quickTradeGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  quickTradeButton: {
    width: '48%',
    borderWidth: 2,
    borderRadius: 10,
    padding: 15,
    marginBottom: 10,
    alignItems: 'center',
  },
  quickTradeText: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  symbolText: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 3,
  },
  priceText: {
    fontSize: 14,
    marginBottom: 3,
  },
  changeText: {
    fontSize: 12,
    fontWeight: 'bold',
  },
  voiceControl: {
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#E3F2FD',
    borderRadius: 10,
    marginBottom: 15,
  },
  voiceButton: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#2196F3',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 10,
  },
  voiceButtonActive: {
    backgroundColor: '#F44336',
  },
  voiceButtonText: {
    fontSize: 24,
  },
  transcript: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
  },
  summaryCards: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  summaryCard: {
    width: '30%',
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
  },
  summaryCardTitle: {
    fontSize: 12,
    color: '#666',
    marginBottom: 5,
  },
  summaryCardValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
  },
  notificationItem: {
    backgroundColor: '#FFF3E0',
    padding: 10,
    borderRadius: 5,
    marginBottom: 10,
  },
  notificationTitle: {
    fontWeight: 'bold',
    marginBottom: 3,
  },
  notificationMessage: {
    fontSize: 12,
    color: '#666',
  },
});

export default AGStockMobile;