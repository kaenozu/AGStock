from typing import List, Callable, Tuple, Optional
import streamlit as st


# 各タブのレンダリング関数を遅延インポートするためのラッパー
def render_dashboard_tab():
    from src.simple_dashboard import create_simple_dashboard

    create_simple_dashboard()


def render_performance_tab():
    from src.ui.performance_analyst import render_performance_analyst

    render_performance_analyst()


def render_ai_hub_tab():
    from src.ui.ai_hub import render_ai_hub

    render_ai_hub()


def render_trading_tab(sidebar_config, strategies):
    from src.ui.trading_hub import render_trading_hub

    render_trading_hub(sidebar_config, strategies)


def render_lab_tab():
    from src.ui.lab_hub import render_lab_hub

    render_lab_hub()


def render_tournament_tab():
    from src.ui.tournament_ui import render_tournament_ui

    render_tournament_ui()


def render_prediction_tab():
    from src.prediction_dashboard import create_prediction_analysis_dashboard
    
    create_prediction_analysis_dashboard()


def render_mission_control_tab():
    from src.ui.mission_control import render_mission_control

    render_mission_control()


class DashboardRouter:
    """
    ダッシュボードのタブ構成とルーティングを管理するクラス
    """

    @staticmethod
    def get_tabs(signal_count: int = 0) -> List[Tuple[str, Callable]]:
        """
        現在のコンテキストに基づいて表示すべきタブのリスト（タイトル、レンダラー）を返す
        """
        trading_badge = f" ({signal_count})" if signal_count > 0 else ""

        # タブ定義: (表示名, レンダリング関数)
        tabs = [
            ("🏠 ダッシュボード", render_dashboard_tab),
            ("📈 運用パフォーマンス", render_performance_tab),
            ("📊 市場分析センター", render_ai_hub_tab),
            (f"💼 トレーディング{trading_badge}", render_trading_tab),
            ("🧪 戦略研究所", render_lab_tab),
            ("🎯 予測精度分析", render_prediction_tab),
            ("🏆 シャドウ・トーナメント", render_tournament_tab),
            ("🚀 Mission Control", render_mission_control_tab),
        ]

        return tabs
