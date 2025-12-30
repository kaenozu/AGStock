import logging
import random
from collections import deque
import numpy as np

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
except ImportError:

    class MockTorch:
        def __getattr__(self, name):
            return object

    torch = MockTorch()
    nn = MockTorch()
    optim = MockTorch()

    logger = logging.getLogger(__name__)


class QNetwork(nn.Module):
    #     """Q-Network: 状態から各行動のQ値を予測するニューラルネットワーク"""

    def __init__(self, state_size: int, action_size: int, hidden_size: int = 64):
        super(QNetwork, self).__init__()
        self.fc1 = nn.Linear(state_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.fc3 = nn.Linear(hidden_size, action_size)
        self.relu = nn.ReLU()

    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        return self.fc3(x)


class DQNAgent:
    #     """Deep Q-Network Agent"""

    def __init__(
        self,
        state_size: int,
        action_size: int,
        hidden_size: int = 64,
        learning_rate: float = 0.001,
    ):
        self.state_size = state_size
        self.action_size = action_size
        self.memory = deque(maxlen=2000)
        self.gamma = 0.95
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.batch_size = 32

        if hasattr(torch, "cuda"):
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.model = QNetwork(state_size, action_size, hidden_size).to(self.device)
            self.target_model = QNetwork(state_size, action_size, hidden_size).to(
                self.device
            )
            self.update_target_model()
            self.optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
            self.criterion = nn.MSELoss()
            logger.info(f"DQN Agent initialized on {self.device}")

    def update_target_model(self):
        self.target_model.load_state_dict(self.model.state_dict())

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def act(self, state):
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        with torch.no_grad():
            act_values = self.model(state_tensor)
        return torch.argmax(act_values).item()

    def replay(self):
        if len(self.memory) < self.batch_size:
            return
        minibatch = random.sample(self.memory, self.batch_size)
        states = torch.FloatTensor(np.array([i[0] for i in minibatch])).to(self.device)
        actions = (
            torch.LongTensor(np.array([i[1] for i in minibatch]))
            .unsqueeze(1)
            .to(self.device)
        )
        rewards = torch.FloatTensor(np.array([i[2] for i in minibatch])).to(self.device)
        next_states = torch.FloatTensor(np.array([i[3] for i in minibatch])).to(
            self.device
        )
        dones = torch.FloatTensor(np.array([i[4] for i in minibatch])).to(self.device)

        current_q = self.model(states).gather(1, actions).squeeze(1)
        with torch.no_grad():
            max_next_q = self.target_model(next_states).max(1)[0]
            target_q = rewards + (self.gamma * max_next_q * (1 - dones))

        loss = self.criterion(current_q, target_q)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
