import pytest
from unittest.mock import patch, MagicMock
import sys
from agstock import main

def test_cli_help():
    with patch.object(sys, 'argv', ['agstock.py', '--help']):
        with pytest.raises(SystemExit):
            main()

def test_cli_run():
    with patch.object(sys, 'argv', ['agstock.py', 'run']), \
         patch('auto_trader.run_auto_trader') as mock_run:
        main()
        mock_run.assert_called_once()

def test_cli_backtest():
    with patch.object(sys, 'argv', ['agstock.py', 'backtest']), \
         patch('backtest_report.generate_backtest_report') as mock_report:
        main()
        mock_report.assert_called_once()

def test_cli_backup():
    with patch.object(sys, 'argv', ['agstock.py', 'backup']), \
         patch('backup.backup_data') as mock_backup:
        main()
        mock_backup.assert_called_once()
