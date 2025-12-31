"""
AGStock Mobile Application
"""

import kivy
kivy.require('2.0.0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
import asyncio
import threading
import json
from datetime import datetime

# Import AGStock modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.realtime import RealtimeDataClient
from src.paper_trader import PaperTrader


class AGStockMobileApp(App):
    def build(self):
        self.title = 'AGStock Mobile'
        
        # Main layout
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Header
        header = Label(
            text='AGStock モバイル',
            size_hint_y=None,
            height=50,
            font_size='24sp'
        )
        main_layout.add_widget(header)
        
        # Portfolio summary
        self.portfolio_label = Label(
            text='ポートフォリオ情報を読み込み中...',
            size_hint_y=None,
            height=100,
            text_size=(None, None)
        )
        main_layout.add_widget(self.portfolio_label)
        
        # Real-time data display
        self.realtime_label = Label(
            text='リアルタイムデータを待機中...',
            size_hint_y=None,
            height=150,
            text_size=(None, None)
        )
        main_layout.add_widget(self.realtime_label)
        
        # Market data scroll view
        self.scroll_view = ScrollView()
        self.market_grid = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.market_grid.bind(minimum_height=self.market_grid.setter('height'))
        self.scroll_view.add_widget(self.market_grid)
        main_layout.add_widget(self.scroll_view)
        
        # Chat input
        chat_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        self.chat_input = TextInput(
            hint_text='質問を入力...',
            multiline=False,
            size_hint_x=0.8
        )
        chat_button = Button(
            text='送信',
            size_hint_x=0.2
        )
        chat_button.bind(on_press=self.send_chat_message)
        chat_layout.add_widget(self.chat_input)
        chat_layout.add_widget(chat_button)
        main_layout.add_widget(chat_layout)
        
        # Chat history
        self.chat_history = Label(
            text='チャット履歴',
            size_hint_y=None,
            height=100,
            text_size=(None, None)
        )
        main_layout.add_widget(self.chat_history)
        
        # Initialize components
        self.realtime_client = None
        self.realtime_data = {}
        self.chat_messages = []
        
        # Start background tasks
        self.start_background_tasks()
        
        # Schedule periodic updates
        Clock.schedule_interval(self.update_portfolio, 10)  # Update every 10 seconds
        Clock.schedule_interval(self.update_realtime_display, 1)  # Update every second
        
        return main_layout
    
    def start_background_tasks(self):
        """Start background tasks"""
        # Start realtime client in separate thread
        def start_realtime_client():
            self.realtime_client = RealtimeDataClient()
            
            async def handle_market_data(data):
                self.realtime_data = data
            
            self.realtime_client.register_data_handler("market_data", handle_market_data)
            asyncio.run(self.realtime_client.connect())
        
        realtime_thread = threading.Thread(target=start_realtime_client, daemon=True)
        realtime_thread.start()
    
    def update_portfolio(self, dt):
        """Update portfolio information"""
        try:
            pt = PaperTrader()
            balance = pt.get_current_balance()
            
            portfolio_text = f"""ポートフォリオサマリー:
総資産: {balance.get('total_equity', 0):,.0f}円
現金: {balance.get('cash', 0):,.0f}円
含み損益: {balance.get('unrealized_pnl', 0):,.0f}円"""
            
            self.portfolio_label.text = portfolio_text
        except Exception as e:
            self.portfolio_label.text = f"ポートフォリオ情報取得エラー: {str(e)}"
    
    def update_realtime_display(self, dt):
        """Update real-time data display"""
        try:
            if self.realtime_data:
                data = self.realtime_data.get("data", {})
                timestamp = self.realtime_data.get("timestamp", "")
                
                realtime_text = f"""リアルタイムデータ ({timestamp}):
"""
                
                for symbol, values in data.items():
                    realtime_text += f"{symbol}: {values.get('price', 0):.2f}円 ({values.get('change', 0):+.2f}%)\n"
                
                self.realtime_label.text = realtime_text
                
                # Update market grid
                self.market_grid.clear_widgets()
                for symbol, values in data.items():
                    symbol_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=80)
                    symbol_layout.add_widget(Label(text=f"[b]{symbol}[/b]", markup=True, size_hint_y=None, height=30))
                    symbol_layout.add_widget(Label(text=f"価格: {values.get('price', 0):.2f}円", size_hint_y=None, height=25))
                    symbol_layout.add_widget(Label(text=f"変化: {values.get('change', 0):+.2f}%", size_hint_y=None, height=25))
                    self.market_grid.add_widget(symbol_layout)
            else:
                self.realtime_label.text = "リアルタイムデータを待機中..."
        except Exception as e:
            self.realtime_label.text = f"リアルタイムデータ表示エラー: {str(e)}"
    
    def send_chat_message(self, instance):
        """Send chat message"""
        message = self.chat_input.text.strip()
        if message:
            # Add to chat history
            self.chat_messages.append(f"あなた: {message}")
            self.chat_input.text = ""
            
            # Process message (placeholder for AI response)
            response = f"Ghostwriter: ご質問ありがとうございます。「{message}」についての詳細な分析を準備しています。"
            self.chat_messages.append(response)
            
            # Update chat history display
            self.chat_history.text = "\n".join(self.chat_messages[-5:])  # Show last 5 messages


if __name__ == '__main__':
    AGStockMobileApp().run()
