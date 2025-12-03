"""
Enhanced Backtest Visualizer - バックテスト可視化強化

ドローダウンチャート、月次リターン分布、ローリングシャープレシオなどを生成
"""
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict
import logging


class BacktestVisualizer:
    """バックテスト結果の高度な可視化"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_drawdown(self, equity_curve: pd.Series) -> pd.DataFrame:
        """
        ドローダウンを計算
        
        Args:
            equity_curve: 資産曲線（Series）
            
        Returns:
            ドローダウン情報（DataFrame）
        """
        # 累積最大値
        cumulative_max = equity_curve.expanding().max()
        
        # ドローダウン（金額）
        drawdown_amount = equity_curve - cumulative_max
        
        # ドローダウン（%）
        drawdown_pct = (drawdown_amount / cumulative_max) * 100
        
        return pd.DataFrame({
            'equity': equity_curve,
            'cumulative_max': cumulative_max,
            'drawdown_amount': drawdown_amount,
            'drawdown_pct': drawdown_pct
        })
    
    def create_drawdown_chart(self, equity_curve: pd.Series, 
                            title: str = "ドローダウンチャート") -> go.Figure:
        """
        ドローダウンチャートを作成
        
        Args:
            equity_curve: 資産曲線
            title: グラフタイトル
            
        Returns:
            Plotly Figure
        """
        dd_data = self.calculate_drawdown(equity_curve)
        
        # 2段組みグラフを作成
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            row_heights=[0.6, 0.4],
            subplot_titles=("資産推移", "ドローダウン（%）")
        )
        
        # 資産曲線
        fig.add_trace(
            go.Scatter(
                x=dd_data.index,
                y=dd_data['equity'],
                name="資産",
                line=dict(color='#00D9FF', width=2)
            ),
            row=1, col=1
        )
        
        # 累積最大値（点線）
        fig.add_trace(
            go.Scatter(
                x=dd_data.index,
                y=dd_data['cumulative_max'],
                name="過去最大",
                line=dict(color='gray', width=1, dash='dash'),
                opacity=0.5
            ),
            row=1, col=1
        )
        
        # ドローダウン（面グラフ）
        fig.add_trace(
            go.Scatter(
                x=dd_data.index,
                y=dd_data['drawdown_pct'],
                name="ドローダウン",
                fill='tozeroy',
                fillcolor='rgba(255, 68, 68, 0.3)',
                line=dict(color='#FF4444', width=2)
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            title=title,
            height=600,
            hovermode='x unified',
            template='plotly_dark',
            showlegend=True
        )
        
        fig.update_yaxes(title_text="資産 (円)", row=1, col=1)
        fig.update_yaxes(title_text="DD (%)", row=2, col=1)
        fig.update_xaxes(title_text="日付", row=2, col=1)
        
        return fig
    
    def calculate_monthly_returns(self, equity_curve: pd.Series) -> pd.DataFrame:
        """
        月次リターンを計算
        
        Args:
            equity_curve: 資産曲線
            
        Returns:
            月次リターンのDataFrame
        """
        # 月次リサンプリング
        monthly_equity = equity_curve.resample('M').last()
        
        # 月次リターン計算
        monthly_returns = monthly_equity.pct_change().dropna() * 100
        
        return pd.DataFrame({
            'year': monthly_returns.index.year,
            'month': monthly_returns.index.month,
            'return': monthly_returns.values
        })
    
    def create_monthly_returns_heatmap(self, equity_curve: pd.Series,
                                      title: str = "月次リターン分布") -> go.Figure:
        """
        月次リターンのヒートマップを作成
        
        Args:
            equity_curve: 資産曲線
            title: グラフタイトル
            
        Returns:
            Plotly Figure
        """
        monthly_data = self.calculate_monthly_returns(equity_curve)
        
        # ピボットテーブル作成
        pivot_table = monthly_data.pivot(index='year', columns='month', values='return')
        
        # 月名
        month_names = ['1月', '2月', '3月', '4月', '5月', '6月',
                      '7月', '8月', '9月', '10月', '11月', '12月']
        
        fig = go.Figure(data=go.Heatmap(
            z=pivot_table.values,
            x=month_names,
            y=pivot_table.index,
            colorscale='RdYlGn',
            zmid=0,
            text=np.round(pivot_table.values, 2),
            texttemplate='%{text}%',
            textfont={"size": 10},
            hoverongaps=False,
            colorbar=dict(title="リターン (%)")
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title="月",
            yaxis_title="年",
            height=400,
            template='plotly_dark'
        )
        
        return fig
    
    def calculate_rolling_sharpe(self, returns: pd.Series, 
                                window: int = 60) -> pd.Series:
        """
        ローリングシャープレシオを計算
        
        Args:
            returns: リターン系列
            window: ウィンドウサイズ（日数）
            
        Returns:
            ローリングシャープレシオ
        """
        # ローリング平均リターン（年率化）
        rolling_mean = returns.rolling(window=window).mean() * 252
        
        # ローリング標準偏差（年率化）
        rolling_std = returns.rolling(window=window).std() * np.sqrt(252)
        
        # シャープレシオ
        rolling_sharpe = rolling_mean / rolling_std
        
        return rolling_sharpe.dropna()
    
    def create_rolling_sharpe_chart(self, returns: pd.Series, window: int = 60,
                                   title: str = "ローリングシャープレシオ") -> go.Figure:
        """
        ローリングシャープレシオのチャートを作成
        
        Args:
            returns: リターン系列
            window: ウィンドウサイズ
            title: グラフタイトル
            
        Returns:
            Plotly Figure
        """
        rolling_sharpe = self.calculate_rolling_sharpe(returns, window)
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=rolling_sharpe.index,
            y=rolling_sharpe,
            name=f"{window}日ローリング",
            line=dict(color='#00D9FF', width=2),
            fill='tozeroy',
            fillcolor='rgba(0, 217, 255, 0.1)'
        ))
        
        # ゼロライン
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        
        # 良好ライン（1.0）
        fig.add_hline(y=1.0, line_dash="dot", line_color="green", opacity=0.5,
                     annotation_text="良好", annotation_position="right")
        
        fig.update_layout(
            title=title,
            xaxis_title="日付",
            yaxis_title="シャープレシオ",
            height=400,
            hovermode='x unified',
            template='plotly_dark'
        )
        
        return fig
    
    def create_comprehensive_report(self, equity_curve: pd.Series, 
                                   returns: pd.Series) -> Dict[str, go.Figure]:
        """
        包括的なバックテストレポートを生成
        
        Args:
            equity_curve: 資産曲線
            returns: リターン系列
            
        Returns:
            各種グラフの辞書
        """
        charts = {}
        
        try:
            charts['drawdown'] = self.create_drawdown_chart(equity_curve)
        except Exception as e:
            self.logger.error(f"Drawdown chart error: {e}")
        
        try:
            charts['monthly_returns'] = self.create_monthly_returns_heatmap(equity_curve)
        except Exception as e:
            self.logger.error(f"Monthly returns heatmap error: {e}")
        
        try:
            charts['rolling_sharpe'] = self.create_rolling_sharpe_chart(returns)
        except Exception as e:
            self.logger.error(f"Rolling Sharpe chart error: {e}")
        
        return charts


if __name__ == "__main__":
    # テスト実行
    logging.basicConfig(level=logging.INFO)
    
    # ダミーデータ作成
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=365)
    returns = pd.Series(np.random.randn(365) * 0.01, index=dates)
    
    # 資産曲線を生成
    initial_capital = 10000000
    equity_curve = (1 + returns).cumprod() * initial_capital
    
    # 可視化
    visualizer = BacktestVisualizer()
    
    print("=== バックテスト可視化 ===\n")
    
    # ドローダウン情報
    dd_data = visualizer.calculate_drawdown(equity_curve)
    max_dd = dd_data['drawdown_pct'].min()
    print(f"最大ドローダウン: {max_dd:.2f}%\n")
    
    # グラフ生成
    charts = visualizer.create_comprehensive_report(equity_curve, returns)
    print(f"生成されたグラフ数: {len(charts)}")
    
    # グラフを保存（オプション）
    for name, fig in charts.items():
        fig.write_html(f"backtest_{name}.html")
        print(f"保存: backtest_{name}.html")
