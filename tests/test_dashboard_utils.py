"""
dashboard_utilsのテスト
"""

import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.dashboard_utils import check_and_execute_missed_trades


@pytest.fixture
def mock_streamlit():
    """Streamlitのモック"""
    with patch("src.dashboard_utils.st") as mock_st:
        # session_stateを辞書かつ属性アクセス可能なオブジェクトにする
        class SessionState(dict):
            def __getattr__(self, key):
                try:
                    return self[key]
                except KeyError:
                    raise AttributeError(key)

            def __setattr__(self, key, value):
                self[key] = value

        mock_st.session_state = SessionState()
        yield mock_st


@pytest.fixture
def mock_paper_trader():
    """PaperTraderのモック"""
    with patch("src.dashboard_utils.PaperTrader") as mock_pt_cls:
        yield mock_pt_cls


@patch("src.dashboard_utils.subprocess.run")
def test_check_and_execute_missed_trades_already_checked(mock_run, mock_streamlit, mock_paper_trader):
    """既にチェック済みの場合は何もしない"""
    mock_streamlit.session_state["auto_trade_checked"] = True

    check_and_execute_missed_trades()

    mock_paper_trader.assert_not_called()
    mock_run.assert_not_called()


@patch("src.dashboard_utils.subprocess.run")
def test_check_and_execute_missed_trades_no_history(mock_run, mock_streamlit, mock_paper_trader):
    """履歴がない場合は実行する"""
    mock_pt = mock_paper_trader.return_value
    mock_pt.get_trade_history.return_value = pd.DataFrame()

    # 実行成功を模倣
    mock_run.return_value.returncode = 0

    check_and_execute_missed_trades()

    assert mock_streamlit.session_state["auto_trade_checked"] is True
    mock_run.assert_called_once()
    mock_streamlit.success.assert_called()


@patch("src.dashboard_utils.subprocess.run")
def test_check_and_execute_missed_trades_executed_today(mock_run, mock_streamlit, mock_paper_trader):
    """今日既に実行済みの場合は実行しない"""
    mock_pt = mock_paper_trader.return_value

    today = datetime.date.today()
    history = pd.DataFrame({"date": [today]})
    mock_pt.get_trade_history.return_value = history

    check_and_execute_missed_trades()

    mock_run.assert_not_called()


@patch("src.dashboard_utils.subprocess.run")
def test_check_and_execute_missed_trades_missed(mock_run, mock_streamlit, mock_paper_trader):
    """未実行の場合は実行する（平日かつ昨日以前）"""
    mock_pt = mock_paper_trader.return_value

    # 昨日を最終取引日とする
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    history = pd.DataFrame({"date": [yesterday]})
    mock_pt.get_trade_history.return_value = history

    # 今日が平日であることを強制するためにdatetime.date.todayをモックする必要があるが、
    # ここでは簡易的に、もし今日が土日なら実行されないことを許容するか、
    # datetimeをモックする。

    # datetimeをモックして平日（月曜=0）にする
    with patch("src.dashboard_utils.datetime") as mock_datetime:
        mock_datetime.date.today.return_value = datetime.date(2023, 1, 2)  # 月曜日
        mock_datetime.date.side_effect = datetime.date

        # 履歴の日付も調整（金曜日）
        last_trade = datetime.date(2022, 12, 30)
        history = pd.DataFrame({"date": [last_trade]})
        mock_pt.get_trade_history.return_value = history

        mock_run.return_value.returncode = 0

        check_and_execute_missed_trades()

        mock_run.assert_called_once()


@patch("src.dashboard_utils.subprocess.run")
def test_check_and_execute_missed_trades_error(mock_run, mock_streamlit, mock_paper_trader):
    """実行エラーのハンドリング"""
    mock_pt = mock_paper_trader.return_value
    mock_pt.get_trade_history.return_value = pd.DataFrame()

    # 実行失敗
    mock_run.return_value.returncode = 1
    mock_run.return_value.stderr = "Error"

    check_and_execute_missed_trades()

    mock_streamlit.error.assert_called()


def test_check_and_execute_missed_trades_exception(mock_streamlit, mock_paper_trader):
    """例外発生時のハンドリング"""
    mock_paper_trader.side_effect = Exception("DB Error")

    # 例外が発生してもクラッシュしないこと
    check_and_execute_missed_trades()
