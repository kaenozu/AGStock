# """
# 高度なリスク管理クラス
#     Value at Risk (VaR), Conditional VaR (CVaR), ストレステスト、リスクパリティウェイトの計算などを行う。
import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List
# yfinance が使用される場合は、ここでインポート
try:
    pass
import yfinance as yf
YFINANCE_AVAILABLE = True
except ImportError:
    yf = None  # yfinanceがなければNoneとして扱う
    YFINANCE_AVAILABLE = False
from src.data_loader import fetch_stock_data
# """
# 
# 
class AdvancedRiskManager:
#     """
#     投資ポートフォリオの高度なリスクを評価・管理するためのクラス。
#     - VaR (Value at Risk)
#     - CVaR (Conditional VaR / Expected Shortfall)
#     - ポトレステスト
#     - リスクパリティ最適化
#     - 相関・ボラティリティ調整
#     - シナリオ分析
#     """

def __init__(self, config: Dict = None):
        pass
        self.config = config or {}
        self.max_daily_loss_pct = self.config.get("auto_trading", {}).get(
            "max_daily_loss_pct", -3.0
        )
        self.market_crash_threshold = self.config.get("auto_trading", {}).get(
            "market_crash_threshold", -3.0
        )
        self.max_correlation = self.config.get("auto_trading", {}).get(
            "max_correlation", 0.7
        )
        # 他の初期化
        self.confidence_level = self.config.get("var_confidence_level", 0.05)
        self.historical_returns = None

    def check_drawdown_protection(self, paper_trader, logger):
        pass
#         """
#                 ドローダウン保護をチェック
#                     Args:
#                         paper_trader: PaperTraderのインスタンス
#                     logger: ログ出力用のロガー
#                     Returns:
#                         tuple: (is_safe: bool, reason: str, signals: List[dict])
#                         # 資産履歴を取得
#                 equity_history = paper_trader.get_equity_history()
#                     if equity_history.empty:
#                         # 履歴がない場合（初日など）
#                     return True, "履歴不足のためスキップ", []
#         # 最新2日間の資産額を取得
#                 equity_history = equity_history.sort_values(by="date", ascending=False)
#                 recent_equities = equity_history.head(2)["total_equity"].values
#                     if len(recent_equities) < 2:
#                         # 2日分のデータがない場合
#                     return True, "十分な履歴がないためスキップ", []
#                     current_equity = recent_equities[0]
#                 previous_equity = recent_equities[1]
#         # 1日分の損益率を計算
#                 daily_change_pct = (current_equity - previous_equity) / previous_equity * 100
#         # 損益率が閾値を超えていれば危険
#                 if daily_change_pct < self.max_daily_loss_pct:
#                     # 危険なため、現在のポジションをすべて売却するシグナルを生成
#                     signals = []
#                     current_positions = paper_trader.get_positions()
#                     for ticker in current_positions.index:
#                         signals.append(
#                             {
#                                 "ticker": ticker,
#                                 "action": "SELL",
#                                 "reason": f"Drawdown protection triggered. Daily loss: {daily_change_pct:.2f}% exceeded threshold: {self.max_daily_loss_pct:.2f}%",
#                                 "strategy": "Drawdown Protection",
#                             }
#                         )
#                         logger.warning(
#                         f"Drawdown protection triggered. Daily loss: {daily_change_pct:.2f}% exceeded threshold: {self.max_daily_loss_pct:.2f}%"
#                     )
#         # 日本語のreasonを設定
#                     reason_jp = f"損失率が{self.max_daily_loss_pct:.2f}%を超過しています。緊急決済します。"
#                     return False, reason_jp, signals
#                     return True, "OK", []
#         """

def check_market_crash(self, logger):
        pass
#         """
#                 主要市場の急落を検出 (テストコードに合わせて名前を変更)
#                     Args:
#                         logger: ログ出力用のロガー
#                     Returns:
#                         tuple: (allow_buy: bool, reason: str)
#                         if not YFINANCE_AVAILABLE:
#                             logger.warning("yfinance not available, skipping market crash detection.")
#         # yfinanceがない場合は、クラッシュしていないと仮定してTrueを返す
#                     return True, "yfinance not available, クラッシュ検出をスキップします。"
#         # 主要市場のシンボル
#                 markets = {
#                     "^N225": "日経平均",  # 日経225
#                     "^GSPC": "S&P500",  # S&P 500
#                     "^DJI": "ダウ平均",  # Dow Jones Industrial Average
#                 }
#                     for symbol, name in markets.items():
#                         try:
#                             # 直近2日のデータを取得
#                         hist = yf.Ticker(symbol).history(period="5d")  # 5日間を取って最新2日分を使う
#                         if len(hist) < 2:
#                             logger.warning(f"Not enough data for {symbol}")
#                             continue
#         # 2日前と昨日の終値を比較 (最新の2点)
#                         recent_close = hist["Close"].tail(2).values
#                         day_before_yesterday_close = recent_close[0]
#                         yesterday_close = recent_close[1]
#                             daily_change_pct = (yesterday_close - day_before_yesterday_close) / day_before_yesterday_close * 100
#         # 閾値を下回っていたらクラッシュと判定
#         # market_crash_threshold は百分率で保存されているため、100倍は不要
#                         if daily_change_pct < self.market_crash_threshold:
#                             reason = f"{name} ({symbol}) が前日比で{daily_change_pct:.2f}%急落し、クラッシュ検知閾値({self.market_crash_threshold:.2f}%)を下回りました。"
#                             logger.warning(reason)
#                             return False, reason
#                         except Exception as e:
#                             logger.error(f"Error fetching data for {symbol}: {e}")
#         # エラー時は処理を続ける（他の市場をチェック）
#         # すべての市場が閾値以上であればクラッシュなし
#                 return True, "正常な市場条件です。"
#         """

def check_correlation(self, ticker, existing_positions: List[str], logger):
        pass
        print(
            f"DEBUG: check_correlation called with ticker={ticker}, existing_positions={existing_positions}"
        )
        # 既存ポジションがなければOK
        # 銘柄リストを結合
        all_tickers = [ticker] + existing_positions
        unique_tickers = list(set(all_tickers))  # 重複を排除
        # 価格データを取得
        # fetch_stock_data は Dict[ticker, DataFrame] を返す想定
        # データ取得失敗時は、リスクをとって許可する（テストの意図）
        # データマップがなければスキップ
        # 各銘柄のリターンを計算
        returns_map = {}
        for tkr, df in data_map.items():
            if df is not None and not df.empty and "Close" in df.columns:
                # 終値リターン
                df["Return"] = df["Close"].pct_change()
                returns_map[tkr] = df["Return"].dropna()
            else:
                logger.warning(f"No valid price data for {tkr}")
                returns_map[tkr] = pd.Series(dtype=float)  # 空のSeries
            if ticker not in returns_map or returns_map[ticker].empty:
                pass
            logger.warning(f"No return data for new ticker: {ticker}")
            return False, f"{ticker} のデータが不足しています。"
        # 新しい銘柄のリターン
        new_returns = returns_map[ticker]
        # 既存の各銘柄との相関を計算
        for existing_ticker in existing_positions:
            print(f"DEBUG: Processing existing ticker: {existing_ticker}")
            if existing_ticker not in returns_map or returns_map[existing_ticker].empty:
                logger.warning(f"No return data for existing ticker: {existing_ticker}")
                continue
                existing_returns = returns_map[existing_ticker]
            # デバッグ: new_returns と existing_returns の内容を確認
            print(f"DEBUG: new_returns for {ticker}: {new_returns.head()}")
            print(
                f"DEBUG: existing_returns for {existing_ticker}: {existing_returns.head()}"
            )
            # 共通の日付で計算
            common_dates = new_returns.index.intersection(existing_returns.index)
            if len(common_dates) < 5:  # 少なくとも5日分は必要
                logger.info(
                    f"Not enough common dates for {ticker}-{existing_ticker}: {len(common_dates)}"
                )
                continue
                new_common = new_returns.loc[common_dates]
            existing_common = existing_returns.loc[common_dates]
            # 相関係数を計算
            print(f"DEBUG: Calculating correlation for {ticker} vs {existing_ticker}")
            correlation = new_common.corr(existing_common)
            print(f"DEBUG: Correlation value: {correlation}, type: {type(correlation)}")
            # デバッグ出力を追加
            logger.debug(
                f"Correlation calc: ticker={ticker}, existing_ticker={existing_ticker}, correlation={correlation}, abs(correlation)={abs(correlation)}, threshold={self.max_correlation}, condition={abs(correlation) > self.max_correlation}"
            )
            # 相関が計算できない場合 (例: すべて同じ値)
            # 両者が非常に似ている可能性があるため、高相関とみなす。
            # 閾値を超えたら危険
            print(
                f"DEBUG: Checking if abs({correlation}) > {self.max_correlation} -> {abs(correlation) > self.max_correlation}"
            )
            if abs(correlation) > self.max_correlation:
                reason = f"{ticker} と {existing_ticker} の相関係数 ({correlation:.3f}) が閾値 ({self.max_correlation:.2f}) を超えています。相関が高すぎる。"
                logger.warning(reason)
                print(f"DEBUG: High correlation detected, returning False")
                return False, reason
            else:
                print(f"DEBUG: Correlation is within threshold, continuing")
        # すべての既存銘柄との相関が許容範囲内であればOK
        print("DEBUG: All correlations are within threshold. Returning True.")
        return True, f"{ticker} は既存のポジションとの相関が低いです。"

    # --- 以前のVaR、CVaRなどのメソッドも維持 ---
    def calculate_var(self, returns: pd.Series, method: str = "historical") -> float:
        pass
#         """
#         Value at Risk (VaR) を計算
#             Args:
#                 returns (pd.Series): ポートフォリオ収益率
#             method (str): 'historical', 'parametric', 'monte_carlo'
#             Returns:
#                 float: VaR (負の値で返す)
#                 if method == "historical":
#                     var = returns.quantile(self.confidence_level)
#         elif method == "parametric":
#             mu = returns.mean()
#             sigma = returns.std()
#             var = mu + sigma * stats.norm.ppf(self.confidence_level)
#         elif method == "monte_carlo":
#             # 簡略化のため、正規分布に基づくMC
#             mu = returns.mean()
#             sigma = returns.std()
#             simulated_returns = np.random.normal(loc=mu, scale=sigma, size=10000)
#             var = np.percentile(simulated_returns, self.confidence_level * 100)
#         else:
#             raise ValueError(f"Method {method} not supported")
#             return var
#         """

def calculate_cvar(self, returns: pd.Series, method: str = "historical") -> float:
        pass
#         """
#         Conditional VaR (Expected Shortfall) を計算
#             Args:
#                 returns (pd.Series): ポートフォリオ収益率
#             method (str): 'historical', 'parametric'
#             Returns:
#                 float: CVaR (負の値で返す)
#                 var = self.calculate_var(returns, method=method)
#         if method == "historical":
#             tail_losses = returns[returns <= var]
#             cvar = tail_losses.mean() if len(tail_losses) > 0 else var
#         elif method == "parametric":
#             mu = returns.mean()
#             sigma = returns.std()
#             z_alpha = stats.norm.ppf(self.confidence_level)
#             pdf_z_alpha = stats.norm.pdf(z_alpha)
#             cvar = mu + sigma * (pdf_z_alpha / self.confidence_level)
#         else:
#             raise ValueError(f"Method {method} not supported")
#             return cvar
#         """

    def calculate_portfolio_var(
        self, returns: pd.DataFrame, weights: np.ndarray
    ) -> float:
        pass
#         """
#         ポートフォリオ収益率行列とウェイトベクトルからポートフォリオVaRを計算
#             Args:
#                 returns (pd.DataFrame): 各資産の日次収益率
#             weights (np.ndarray): 各資産の投資比率 (合計 = 1.0)
#             Returns:
#                 float: ポートフォリオ全体のVaR
#                 portfolio_returns = (returns * weights).sum(axis=1)
#         portfolio_var = self.calculate_var(portfolio_returns)
#         return portfolio_var
#         """

def _interpret_var(self, var: float) -> str:
#         """VaRの解釈を返す"""
return f"At {self.confidence_level*100:.0f}% confidence, expected loss is {abs(var)*100:.2f}%"

    def stress_test(self, baseline_returns: pd.Series, scenarios: List[Dict]) -> Dict:
        pass
#         """
#         ストレステストを実行
#             Args:
#                 baseline_returns (pd.Series): ベースラインの収益率
#             scenarios (List[Dict]): {"name": str, "shock": float}, e.g., {"name": "2008 Crisis", "shock": -0.1}
#             Returns:
#                 Dict: 各シナリオのVaR, CVaR
#                 results = {}
#         for scenario in scenarios:
#             name = scenario["name"]
#             shock = scenario["shock"]
#             stressed_returns = baseline_returns + shock
#             var = self.calculate_var(stressed_returns)
#             cvar = self.calculate_cvar(stressed_returns)
#             results[name] = {"VaR": var, "CVaR": cvar}
#         return results
#         """

    def calculate_risk_parity_weights(
        self, returns: pd.DataFrame, tolerance: float = 1e-6
    ) -> np.ndarray:
        pass
#         """
#                 リスクパリティによる資産配分ウェイトを計算する (簡略化版)
#                     Args:
    pass
#                         returns (pd.DataFrame): 各資産の日次収益率
#                     tolerance (float): 収束判定の許容誤差
#                     Returns:
    pass
#                         np.ndarray: 風险均等分配のウェイト
#                         n_assets = returns.shape[1]
#                 volatilities = returns.std().values  # 各資産のボラティリティ
#         # 簡易リスクパリティ（ボラティリティの逆数に比例）
#         # 本来は反復計算が必要だが、ここでは単純な逆数で近似
#                 inv_vols = 1.0 / (volatilities + tolerance)  # zero division 防止
#                 weights = inv_vols / inv_vols.sum()
#                 return weights
# 
#         """  # Force Balanced
