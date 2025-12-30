import datetime
from typing import Dict, List


from src.constants import NIKKEI_225_TICKERS, SP500_TICKERS  # 地域判定のため
from src.data_loader import (fetch_fundamental_data, get_latest_price)
from src.ensemble_predictor import EnsemblePredictor, EnhancedEnsemblePredictor  # 中期予測フィルター
from src.sentiment import SentimentAnalyzer
from src.strategies import (CombinedStrategy, DividendStrategy,
                            LightGBMStrategy, MLStrategy)


class MarketScanner:
    """
    市場をスキャンして新規の取引シグナルを検出する機能を提供します。
    """

    def __init__(
        self,
        config: dict,
        paper_trader,
        logger,
        advanced_risk,
        asset_selector,
        position_manager,
        kelly_criterion,
        risk_manager,
    ):
        self.config = config
        self.pt = paper_trader
        self.logger = logger
        self.advanced_risk = advanced_risk
        self.asset_selector = asset_selector
        self.position_manager = position_manager  # _fetch_data_with_retry を使うため
        self.kelly_criterion = kelly_criterion
        self.risk_manager = risk_manager  # regime_multiplier の取得のため

        self.asset_config = self.config.get(
            "assets", {"japan_stocks": True, "us_stocks": True, "europe_stocks": True, "crypto": False, "fx": False}
        )
        self.allow_small_mid_cap = True  # AssetSelectorから引き継ぎ

    def scan_market(self) -> List[Dict]:
        """市場をスキャンして新規シグナルを検出（グローバル分散対応）"""
        self.logger.info("市場スキャン開始...")

        # 🚨 市場急落チェック
        allow_buy_market, market_reason = self.advanced_risk.check_market_crash(self.logger)
        if not allow_buy_market:
            self.logger.warning(f"⚠️ 市場急落のため新規BUY停止: {market_reason}")

        # センチメント分析
        try:
            sa = SentimentAnalyzer()
            sentiment = sa.get_market_sentiment()
            self.logger.info(f"市場センチメント: {sentiment['label']} ({sentiment['score']:.2f})")

            # ネガティブセンチメント時はBUYを抑制
            allow_buy = sentiment["score"] >= -0.2
        except Exception as e:
            self.logger.warning(f"センチメント分析エラー: {e}")
            allow_buy = True

        # 対象銘柄（グローバル分散）
        tickers = self.asset_selector.get_target_tickers()
        self.logger.info(f"対象銘柄数: {len(tickers)}")

        # データ取得（リトライ付き）
        data_map = self.position_manager._fetch_data_with_retry(tickers)

        # データの鮮度を確認・ログ出力
        if data_map:
            sample_ticker = list(data_map.keys())[0]
            sample_df = data_map[sample_ticker]
            if not sample_df.empty:
                data_date = (
                    sample_df.index[-1].strftime("%Y-%m-%d %H:%M")
                    if hasattr(sample_df.index[-1], "strftime")
                    else str(sample_df.index[-1])
                )
                self.logger.info(f"📅 データ基準日時: {data_date} (最新の市場データ)")
                self.logger.info(f"⏰ 判断実行日時: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 戦略初期化
        strategies = [
            ("LightGBM", LightGBMStrategy(lookback_days=365, threshold=0.005)),
            ("ML Random Forest", MLStrategy()),
            ("Combined", CombinedStrategy()),
            ("High Dividend", DividendStrategy()),  # 修正済みの安全な高配当戦略を追加
        ]

        positions = self.pt.get_positions()
        held_tickers = set(positions["ticker"]) if not positions.empty else set()
        signals = []

        for ticker in tickers:
            df = data_map.get(ticker)
            if df is None or df.empty:
                continue

            # 既にポジションを持っているかチェック
            is_held = ticker in held_tickers

            # 各戦略でシグナル生成
            for strategy_name, strategy in strategies:
                try:
                    sig_series = strategy.generate_signals(df)

                    if sig_series.empty:
                        continue

                    last_signal = sig_series.iloc[-1]

                    # BUYシグナル
                    if last_signal == 1 and not is_held and allow_buy:

                        # 📊 銘柄相関チェック
                        existing_tickers = list(held_tickers)
                        allow_corr, corr_reason = self.advanced_risk.check_correlation(
                            ticker, existing_tickers, self.logger
                        )
                        if not allow_corr:
                            self.logger.info(f"  {ticker}: {corr_reason}")
                            continue
                        # ファンダメンタルチェック
                        fundamentals = fetch_fundamental_data(ticker)

                        # 時価総額チェック
                        if not self.asset_selector.filter_by_market_cap(ticker, fundamentals):
                            self.logger.info(f"  {ticker}: 時価総額が小さすぎるためスキップ")
                            continue

                        pe = fundamentals.get("trailingPE") if fundamentals else None

                        # PERが極端に高い場合はスキップ
                        if pe and pe > 50:
                            continue

                        latest_price = get_latest_price(df)

                        # 🔮 中期予測フィルター（新機能）
                        # 短期だけでなく、5日後も上昇が見込める銘柄のみBUY
                        try:
                            predictor = EnhancedEnsemblePredictor()
                            future_result = predictor.predict_trajectory(df, days_ahead=5)

                            if "error" not in future_result:
                                predicted_change_pct = future_result["change_pct"]

                                # 5日後に+0.5%以上の上昇が見込めない場合はスキップ（閾値を緩和）
                                if predicted_change_pct < 0.5:
                                    self.logger.info(
                                        f"  {ticker}: 中期予測が弱い({predicted_change_pct:+.1f}%)ためスキップ"
                                    )
                                    continue
                                else:
                                    self.logger.info(f"  {ticker}: 中期予測OK({predicted_change_pct:+.1f}%) ✅")
                            else:
                                # 予測エラー時は従来通りBUY（保守的に通す）
                                self.logger.warning(f"  {ticker}: 中期予測エラー、従来ロジックで判断")
                        except Exception as e:
                            self.logger.warning(f"  {ticker}: 中期予測失敗 ({e})、従来ロジックで判断")

                        # 地域を判定
                        if ticker in NIKKEI_225_TICKERS:
                            region = "日本"
                        elif ticker in SP500_TICKERS:
                            region = "米国"
                        else:
                            region = "欧州"

                        # Phase 30-3: Kelly Criterion for Position Sizing
                        # Calculate optimal size based on actual trading history
                        balance = self.pt.get_current_balance()
                        equity = balance["total_equity"]
                        cash = balance["cash"]

                        # Calculate actual win rate and win/loss ratio from history
                        try:
                            history = self.pt.get_trade_history()
                            if not history.empty and "realized_pnl" in history.columns:
                                # Filter out trades with zero PnL (still open or just closed at breakeven)
                                closed_trades = history[history["realized_pnl"] != 0]

                                if len(closed_trades) >= 10:  # Need at least 10 trades for meaningful stats
                                    wins = closed_trades[closed_trades["realized_pnl"] > 0]
                                    losses = closed_trades[closed_trades["realized_pnl"] < 0]

                                    win_rate = len(wins) / len(closed_trades)

                                    if len(wins) > 0 and len(losses) > 0:
                                        avg_win = wins["realized_pnl"].mean()
                                        avg_loss = abs(losses["realized_pnl"].mean())
                                        win_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 1.5
                                    else:
                                        win_loss_ratio = 1.5  # Default if no losses yet

                                    self.logger.info(
                                        f"📊 実績ベース Kelly: 勝率={win_rate:.1f}, 損益比={
                                            win_loss_ratio:.2f} (過去{len(closed_trades)}件)"
                                    )
                                else:
                                    # Not enough history, use conservative defaults
                                    win_rate = 0.50  # More conservative than 55%
                                    win_loss_ratio = 1.5
                                    self.logger.info(
                                        f"📊 デフォルト Kelly: 勝率={win_rate:.1f}, 損益比={win_loss_ratio:.2f} (履歴不足)"
                                    )
                            else:
                                win_rate = 0.50
                                win_loss_ratio = 1.5
                                self.logger.info(
                                    f"📊 デフォルト Kelly: 勝率={win_rate:.1f}, 損益比={win_loss_ratio:.2f} (履歴なし)"
                                )
                        except Exception as e:
                            self.logger.warning(f"Kelly計算エラー: {e}")
                            win_rate = 0.50
                            win_loss_ratio = 1.5

                        kelly_pct = self.kelly_criterion.calculate_size(
                            win_rate=win_rate, win_loss_ratio=win_loss_ratio
                        )

                        # Adjust by Regime (DynamicRiskManager)
                        regime_multiplier = self.risk_manager.current_params.get("position_size", 1.0)
                        final_size_pct = kelly_pct * regime_multiplier

                        # Calculate quantity
                        target_amount = equity * final_size_pct
                        target_amount = min(target_amount, cash)  # Cap at cash

                        # 米国株かどうか判定（ティッカーにドットがない、または特定のリストに含まれる）
                        is_us_stock = "." not in ticker

                        if is_us_stock:
                            # 米国株は1株単位
                            quantity = int(target_amount / latest_price)
                            if quantity < 1:
                                # 資金不足でも最低1株は買えるかチェック（積極的モードの場合）
                                if cash >= latest_price:
                                    quantity = 1
                                else:
                                    self.logger.info(
                                        f"  {ticker}: 資金不足のためスキップ (必要: {latest_price:.2f}, 保有: {cash:.2f})"
                                    )
                                    continue
                        else:
                            # 日本株は100株単位
                            quantity = int(target_amount / latest_price / 100) * 100
                            if quantity < 100:
                                # 資金不足でも最低100株は買えるかチェック
                                if cash >= latest_price * 100:
                                    quantity = 100
                                else:
                                    self.logger.info(f"  {ticker}: 算出数量が少なすぎるためスキップ ({quantity})")
                                    continue

                        signals.append(
                            {
                                "ticker": ticker,
                                "action": "BUY",
                                "confidence": 0.85,
                                "price": latest_price,
                                "quantity": quantity,
                                "strategy": strategy_name,
                                "reason": f"{strategy_name}による買いシグナル（{region}）",
                            }
                        )
                        break  # 1銘柄につき1シグナル

                    # SELLシグナル（保有中の場合）
                    elif last_signal == -1 and is_held:
                        latest_price = get_latest_price(df)

                        signals.append(
                            {
                                "ticker": ticker,
                                "action": "SELL",
                                "confidence": 0.85,
                                "price": latest_price,
                                "strategy": strategy_name,
                                "reason": f"{strategy_name}による売りシグナル",
                            }
                        )
                        break

                except Exception as e:
                    self.logger.warning(f"シグナル生成エラー ({ticker}, {strategy_name}): {e}")

        self.logger.info(f"検出シグナル数: {len(signals)}")
        return signals
