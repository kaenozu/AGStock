"""
Load Testing Script for AGStock
Tests system performance under various load conditions.
"""
from locust import HttpUser, task, between
import random

class AGStockUser(HttpUser):
    """Simulates a user interacting with AGStock."""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Called when a simulated user starts."""
        self.tickers = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
    
    @task(3)
    def view_dashboard(self):
        """View main dashboard."""
        self.client.get("/")
    
    @task(2)
    def view_details(self):
        """View details page."""
        self.client.get("/詳細")
    
    @task(2)
    def view_performance(self):
        """View performance page."""
        self.client.get("/パフォーマンス")
    
    @task(1)
    def view_settings(self):
        """View settings page."""
        self.client.get("/設定")
    
    @task(1)
    def view_full_auto(self):
        """View full auto system page."""
        self.client.get("/🤖_フルオートシステム")


class StressTestUser(HttpUser):
    """Simulates heavy load user."""
    
    wait_time = between(0.5, 1)  # Faster interaction
    
    @task
    def rapid_page_switching(self):
        """Rapidly switch between pages."""
        pages = ["/", "/詳細", "/パフォーマンス", "/設定"]
        page = random.choice(pages)
        self.client.get(page)


if __name__ == "__main__":
    import os
    os.system("locust -f tests/load_test.py --host=http://localhost:8501")
