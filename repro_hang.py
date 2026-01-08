
import datetime
from unittest.mock import Mock, patch
from dataclasses import dataclass

# Simplified version of the suspected logic
def daily_reset(current_date=None):
    if current_date is None:
        try:
            now_val = datetime.datetime.now()
            if hasattr(now_val, "date") and callable(now_val.date):
                current_date = now_val.date()
            else:
                current_date = now_val
        except Exception:
            current_date = datetime.date.today()
    
    count = 0
    while hasattr(current_date, "return_value"):
        print(f"Loop {count}: {current_date}")
        current_date = current_date.return_value
        count += 1
        if count > 10:
            print("Detected infinite loop")
            break
    return current_date

def test_repro():
    with patch("datetime.datetime") as mock_datetime:
        # This setup matches the test
        # mock_datetime.now.return_value.date.return_value = datetime.date(2025, 1, 1)
        
        # In the real test:
        # with patch("src.risk_guard.datetime") as mock_datetime:
        #     mock_datetime.now.return_value.date.return_value = date(2025, 1, 1)
        
        m_now = Mock()
        mock_datetime.now.return_value = m_now
        m_date = Mock()
        m_now.date = m_date
        m_date.return_value = datetime.date(2025, 1, 1)
        
        print("Calling daily_reset...")
        res = daily_reset()
        print(f"Result: {res}")

if __name__ == "__main__":
    test_repro()
