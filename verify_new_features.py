
import pandas as pd
import numpy as np
import logging
import sys
import os
import time

# Add src to path if needed (though running from root usually works)
sys.path.append(os.getcwd())

from src.strategies.ml import MLStrategy
from src.rl.agent import DQNAgent
from src.rl.environment import TradingEnvironment
from src.realtime.streamer import marketStreamer

# Setup Mock Data
def create_mock_data(length=100):
    dates = pd.date_range(end=pd.Timestamp.now(), periods=length)
    df = pd.DataFrame(index=dates)
    df['Close'] = np.random.randn(length).cumsum() + 100
    df['Volume'] = np.random.randint(100, 1000, length)
    df['RSI'] = np.random.rand(length) * 100
    df['SMA_Ratio'] = 1.0 + np.random.randn(length) * 0.01
    df['Volatility'] = 0.01 + np.random.rand(length) * 0.01
    df['Ret_1'] = np.random.randn(length) * 0.01
    df['Ret_5'] = np.random.randn(length) * 0.02
    return df

def test_xai():
    print("--- Testing XAI (MLStrategy) ---")
    strategy = MLStrategy()
    df = create_mock_data(100)
    
    # Needs a trained model to explain roughly, but MLStrategy init creates an untrained model.
    # We fit it quickly on dummy data.
    # The generate_signals method handles fit internally if data is sufficient.
    
    # We need to manually trigger fit for explain_prediction to work nicely if we call it directly?
    # Actually explain_prediction checks self.model.
    # Let's force fit.
    try:
        data = df.copy()
        data['Target'] = (data['Close'].shift(-1) > data['Close']).astype(int)
        data = data.iloc[:-1]
        features = strategy.feature_names
        X = data[features]
        y = data['Target']
        strategy.model.fit(X, y)
        print("Mock model fitted.")
        
        explanation = strategy.explain_prediction(df)
        print(f"Explanation result: {explanation}")
        
        if explanation and isinstance(explanation, dict):
            print("✅ XAI (MLStrategy) Passed")
        else:
            print("❌ XAI (MLStrategy) Failed: Empty or invalid result")
            
    except Exception as e:
        print(f"❌ XAI (MLStrategy) Error: {e}")

def test_rl():
    print("\n--- Testing RL (Agent & Env) ---")
    try:
        df = create_mock_data(200) # Needs enough for window if any
        # Env expects numeric DF
        env = TradingEnvironment(df)
        agent = DQNAgent(env.state_size, env.action_space_size)
        
        state = env.reset()
        action = agent.act(state)
        print(f"Initial Action: {action}")
        
        next_state, reward, done, _ = env.step(action)
        print(f"Step Result - Reward: {reward}, Done: {done}")
        
        agent.remember(state, action, reward, next_state, done)
        agent.replay()
        print("Replay (training step) successful.")
        
        print("✅ RL System Passed")
    except Exception as e:
        print(f"❌ RL System Error: {e}")

def test_realtime():
    print("\n--- Testing Real-time Streamer ---")
    try:
        # Mock streamer without actual polling loop to avoid network
        streamer = marketStreamer(["TEST.T"])
        
        received_data = []
        def callback(data):
            received_data.append(data)
            print(f"Callback received: {data}")
            
        streamer.register_callback(callback)
        
        # Simulate notification
        fake_data = {'ticker': 'TEST.T', 'price': 1234.0, 'volume': 100, 'time': pd.Timestamp.now()}
        streamer._notify(fake_data)
        
        time.sleep(0.1)
        
        if len(received_data) == 1 and received_data[0]['price'] == 1234.0:
            print("✅ Real-time Streamer Passed")
        else:
            print("❌ Real-time Streamer Failed to receive data")
            
    except Exception as e:
        print(f"❌ Real-time Streamer Error: {e}")

if __name__ == "__main__":
    test_xai()
    test_rl()
    test_realtime()
