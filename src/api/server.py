"""
AGStock FastAPI Server

内部APIを提供し、UI/外部システムとの連携を実現。
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# グローバルアプリインスタンス
_app: Optional[FastAPI] = None


# === Pydantic Models ===

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str = "1.0.0"


class PortfolioSummary(BaseModel):
    total_equity: float
    cash: float
    invested_amount: float
    unrealized_pnl: float
    position_count: int


class Position(BaseModel):
    ticker: str
    quantity: int
    avg_price: float
    current_price: Optional[float] = None
    unrealized_pnl: Optional[float] = None


class TradeRequest(BaseModel):
    ticker: str
    action: str = Field(..., pattern="^(BUY|SELL)$")
    quantity: int = Field(..., gt=0)
    price: Optional[float] = None
    strategy: Optional[str] = None


class TradeResponse(BaseModel):
    success: bool
    message: str
    order_id: Optional[str] = None


class SignalResponse(BaseModel):
    ticker: str
    signal: int  # 1: BUY, -1: SELL, 0: HOLD
    confidence: float
    strategy: str
    explanation: str


class MarketDataResponse(BaseModel):
    ticker: str
    price: float
    change: float
    change_percent: float
    volume: int
    timestamp: str


class BacktestRequest(BaseModel):
    ticker: str
    strategy: str
    period: str = "1y"
    initial_capital: float = 1000000


class BacktestResponse(BaseModel):
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int


# === Lifespan ===

@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    logger.info("AGStock API starting...")
    # 起動時の初期化
    yield
    # シャットダウン時のクリーンアップ
    logger.info("AGStock API shutting down...")


# === App Factory ===

def create_app() -> FastAPI:
    """FastAPIアプリケーションを作成"""
    app = FastAPI(
        title="AGStock API",
        description="AI-Powered Stock Trading System API",
        version="1.0.0",
        lifespan=lifespan,
    )
    
    # CORS設定
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 本番環境では制限すること
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # ルーターを登録
    register_routes(app)
    
    return app


def get_app() -> FastAPI:
    """シングルトンアプリインスタンスを取得"""
    global _app
    if _app is None:
        _app = create_app()
    return _app


# === Dependencies ===

def get_paper_trader():
    """PaperTraderの依存性注入"""
    from src.paper_trader import PaperTrader
    return PaperTrader()


def get_data_loader():
    """DataLoaderの依存性注入"""
    from src.data_loader import DataLoader
    return DataLoader()


# === Routes ===

def register_routes(app: FastAPI):
    """ルートを登録"""
    
    @app.get("/", response_model=HealthResponse)
    async def root():
        """ヘルスチェック"""
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now().isoformat(),
        )
    
    @app.get("/api/v1/health", response_model=HealthResponse)
    async def health_check():
        """詳細ヘルスチェック"""
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now().isoformat(),
        )
    
    # === Portfolio ===
    
    @app.get("/api/v1/portfolio", response_model=PortfolioSummary)
    async def get_portfolio(pt = Depends(get_paper_trader)):
        """ポートフォリオサマリーを取得"""
        try:
            balance = pt.get_current_balance()
            positions = pt.get_positions()
            return PortfolioSummary(
                total_equity=balance.get("total_equity", 0),
                cash=balance.get("cash", 0),
                invested_amount=balance.get("invested_amount", 0),
                unrealized_pnl=balance.get("unrealized_pnl", 0),
                position_count=len(positions) if not positions.empty else 0,
            )
        except Exception as e:
            logger.error(f"Error getting portfolio: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/v1/positions", response_model=List[Position])
    async def get_positions(pt = Depends(get_paper_trader)):
        """保有ポジション一覧を取得"""
        try:
            positions_df = pt.get_positions()
            if positions_df.empty:
                return []
            
            return [
                Position(
                    ticker=row["ticker"],
                    quantity=int(row["quantity"]),
                    avg_price=float(row["avg_price"]),
                )
                for _, row in positions_df.iterrows()
            ]
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # === Trading ===
    
    @app.post("/api/v1/trade", response_model=TradeResponse)
    async def execute_trade(
        request: TradeRequest,
        pt = Depends(get_paper_trader)
    ):
        """取引を実行"""
        try:
            # 価格を取得（指定がなければ最新価格）
            price = request.price
            if price is None:
                from src.data_loader import get_latest_price
                price = get_latest_price(request.ticker)
                if price is None:
                    raise HTTPException(status_code=400, detail="Could not fetch price")
            
            success = pt.execute_trade(
                ticker=request.ticker,
                action=request.action,
                quantity=request.quantity,
                price=price,
                strategy=request.strategy,
            )
            
            return TradeResponse(
                success=success,
                message="Trade executed" if success else "Trade failed",
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # === Market Data ===
    
    @app.get("/api/v1/market/{ticker}", response_model=MarketDataResponse)
    async def get_market_data(ticker: str):
        """銘柄の市場データを取得"""
        try:
            from src.data_loader import fetch_stock_data
            df = fetch_stock_data(ticker, period="5d")
            
            if df is None or df.empty:
                raise HTTPException(status_code=404, detail="Ticker not found")
            
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest
            
            change = latest["Close"] - prev["Close"]
            change_pct = (change / prev["Close"]) * 100
            
            return MarketDataResponse(
                ticker=ticker,
                price=float(latest["Close"]),
                change=float(change),
                change_percent=float(change_pct),
                volume=int(latest["Volume"]),
                timestamp=str(latest.name),
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # === Signals ===
    
    @app.get("/api/v1/signals/{ticker}", response_model=SignalResponse)
    async def get_signal(
        ticker: str,
        strategy: str = Query(default="LightGBM"),
    ):
        """銘柄のシグナルを取得"""
        try:
            from src.data_loader import fetch_stock_data
            from src.strategies import LightGBMStrategy, RSIStrategy, SMACrossoverStrategy
            
            # 戦略を選択
            strategy_map = {
                "LightGBM": LightGBMStrategy,
                "RSI": RSIStrategy,
                "SMA": SMACrossoverStrategy,
            }
            
            strategy_cls = strategy_map.get(strategy, LightGBMStrategy)
            strat = strategy_cls()
            
            # データ取得
            df = fetch_stock_data(ticker, period="1y")
            if df is None or df.empty:
                raise HTTPException(status_code=404, detail="Data not found")
            
            # シグナル生成
            result = strat.analyze(df)
            
            return SignalResponse(
                ticker=ticker,
                signal=result.get("signal", 0),
                confidence=result.get("confidence", 0.0),
                strategy=strategy,
                explanation=strat.get_signal_explanation(result.get("signal", 0)),
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting signal: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # === Backtest ===
    
    @app.post("/api/v1/backtest", response_model=BacktestResponse)
    async def run_backtest(request: BacktestRequest):
        """バックテストを実行"""
        try:
            from src.data_loader import fetch_stock_data
            from src.backtest_engine import BacktestEngine
            from src.strategies import LightGBMStrategy, RSIStrategy
            
            # 戦略を選択
            strategy_map = {
                "LightGBM": LightGBMStrategy,
                "RSI": RSIStrategy,
            }
            strategy_cls = strategy_map.get(request.strategy, LightGBMStrategy)
            
            # データ取得
            df = fetch_stock_data(request.ticker, period=request.period)
            if df is None or df.empty:
                raise HTTPException(status_code=404, detail="Data not found")
            
            # バックテスト実行
            engine = BacktestEngine(initial_capital=request.initial_capital)
            result = engine.run(df, strategy_cls())
            
            if result is None:
                raise HTTPException(status_code=400, detail="Backtest failed")
            
            return BacktestResponse(
                total_return=result.get("total_return", 0),
                sharpe_ratio=result.get("sharpe_ratio", 0),
                max_drawdown=result.get("max_drawdown", 0),
                win_rate=result.get("win_rate", 0),
                total_trades=result.get("total_trades", 0),
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error running backtest: {e}")
            raise HTTPException(status_code=500, detail=str(e))


# === Main ===

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(create_app(), host="0.0.0.0", port=8000)
