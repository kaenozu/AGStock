from typing import List, Dict

# List of Nikkei 225 Tickers (Simplified for initial version to ensure speed)
# In a real app, we might fetch this dynamically or have a fuller list.
# Adding .T for Yahoo Finance Japan compatibility.

NIKKEI_225_TICKERS: List[str] = [
    # === 低価格銘柄（10万円資金向け）===
    # 銀行・金融（200〜400円台）
    "8411.T", # みずほフィナンシャルグループ
    "8308.T", # りそなホールディングス
    "7186.T", # コンコルディア・フィナンシャルグループ
    "8304.T", # あおぞら銀行
    
    # 商社（200〜300円台）
    "2768.T", # 双日
    
    # 通信（400円台）
    "9433.T", # KDDI
    
    # 小売・サービス（100〜300円台）
    "3382.T", # セブン&アイ・ホールディングス
    "8267.T", # イオン
    
    # 不動産（200〜400円台）
    "8801.T", # 三井不動産
    "8802.T", # 三菱地所
    
    # 鉄道（200〜300円台）
    "9001.T", # 東武鉄道
    "9005.T", # 東急
    
    # エネルギー（100〜200円台）
    "5020.T", # ENEOS Holdings
    "1605.T", # Inpex
    
    # === 既存の大型株 ===
    "9432.T", # NTT
    "8306.T", # MUFG
    "8316.T", # SMFG
    "7203.T", # Toyota
    "9984.T", # Softbank Group
    "6758.T", # Sony
    "6861.T", # Keyence
    "6098.T", # Recruit
    "8035.T", # Tokyo Electron
    "9983.T", # Fast Retailing
    "4063.T", # Shin-Etsu Chemical
    "7974.T", # Nintendo
    "6501.T", # Hitachi
    "4502.T", # Takeda
    "7267.T", # Honda
    "8058.T", # Mitsubishi Corp
    "8001.T", # Itochu
    "8766.T", # Tokio Marine
    "6902.T", # Denso
    "6367.T", # Daikin
    "4543.T", # Terumo
    "6954.T", # Fanuc
    "6981.T", # Murata
    "6273.T", # SMC
    "7741.T", # HOYA
    "2914.T", # JT
    "9020.T", # JR East
    "9022.T", # JR Central
    "4452.T", # Kao
    "4661.T", # Oriental Land
    "5401.T", # Nippon Steel
    "7011.T", # Mitsubishi Heavy
    "9101.T", # NYK Line
    "9104.T", # Mitsui O.S.K.
    "9107.T", # Kawasaki Kisen
    "8031.T", # Mitsui & Co
    "8002.T", # Marubeni
    "8591.T", # Orix
]

# Map for human readable names (Optional, but nice to have)
TICKER_NAMES: Dict[str, str] = {
    # 低価格銘柄
    "8411.T": "みずほフィナンシャルグループ",
    "8308.T": "りそなホールディングス",
    "7186.T": "コンコルディア・フィナンシャルグループ",
    "8304.T": "あおぞら銀行",
    "2768.T": "双日",
    "9433.T": "KDDI",
    "3382.T": "セブン&アイ・ホールディングス",
    "8267.T": "イオン",
    "8801.T": "三井不動産",
    "8802.T": "三菱地所",
    "9001.T": "東武鉄道",
    "9005.T": "東急",
    
    # 既存銘柄
    "7203.T": "Toyota Motor",
    "9984.T": "SoftBank Group",
    "6758.T": "Sony Group",
    "6861.T": "Keyence",
    "6098.T": "Recruit Holdings",
    "8035.T": "Tokyo Electron",
    "9983.T": "Fast Retailing",
    "4063.T": "Shin-Etsu Chemical",
    "9432.T": "Nippon Telegraph & Telephone",
    "7974.T": "Nintendo",
    "8306.T": "Mitsubishi UFJ Financial",
    "8316.T": "Sumitomo Mitsui Financial",
    "6501.T": "Hitachi",
    "4502.T": "Takeda Pharmaceutical",
    "7267.T": "Honda Motor",
    "8058.T": "Mitsubishi Corp",
    "8001.T": "Itochu",
    "8766.T": "Tokio Marine",
    "6902.T": "Denso",
    "6367.T": "Daikin Industries",
    "4543.T": "Terumo",
    "6954.T": "Fanuc",
    "6981.T": "Murata Manufacturing",
    "6273.T": "SMC",
    "7741.T": "HOYA",
    "2914.T": "Japan Tobacco",
    "9020.T": "East Japan Railway",
    "9022.T": "Central Japan Railway",
    "4452.T": "Kao",
    "4661.T": "Oriental Land",
    "5401.T": "Nippon Steel",
    "7011.T": "Mitsubishi Heavy Industries",
    "9101.T": "Nippon Yusen",
    "9104.T": "Mitsui O.S.K. Lines",
    "9107.T": "Kawasaki Kisen",
    "1605.T": "Inpex",
    "5020.T": "ENEOS Holdings",
    "8031.T": "Mitsui & Co",
    "8002.T": "Marubeni",
    "8591.T": "Orix",
}

# S&P 500 Top Stocks (US Market)
SP500_TICKERS: List[str] = [
    # Tech Giants (FAANG+)
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA",
    # Finance
    "JPM", "BAC", "WFC", "GS", "MS", "C",
    # Healthcare
    "JNJ", "UNH", "PFE", "ABBV", "TMO", "MRK",
    # Consumer
    "WMT", "HD", "PG", "KO", "PEP", "NKE", "MCD",
    # Industrial
    "BA", "CAT", "GE", "MMM", "HON",
    # Energy
    "XOM", "CVX", "COP",
    # Communication
    "DIS", "NFLX", "CMCSA", "VZ", "T",
]

# STOXX 50 (European Market)
STOXX50_TICKERS: List[str] = [
    # France
    "MC.PA",    # LVMH
    "OR.PA",    # L'Oréal
    "SAN.PA",   # Sanofi
    "TTE.PA",   # TotalEnergies
    "AIR.PA",   # Airbus
    # Germany
    "SAP.DE",   # SAP
    "SIE.DE",   # Siemens
    "VOW3.DE",  # Volkswagen
    "MBG.DE",   # Mercedes-Benz
    "ALV.DE",   # Allianz
    # Netherlands
    "ASML.AS",  # ASML
    "INGA.AS",  # ING
    "PHIA.AS",  # Philips
    # Switzerland
    "NESN.SW",  # Nestlé
    "NOVN.SW",  # Novartis
    "ROG.SW",   # Roche
    # Spain
    "SAN.MC",   # Santander
    "ITX.MC",   # Inditex
    # Italy
    "ENI.MI",   # Eni
]

# Combined universe for global trading
ALL_STOCKS: List[str] = NIKKEI_225_TICKERS + SP500_TICKERS + STOXX50_TICKERS

# Market groupings
MARKETS: Dict[str, List[str]] = {
    "Japan": NIKKEI_225_TICKERS,
    "US": SP500_TICKERS,
    "Europe": STOXX50_TICKERS,
    "All": ALL_STOCKS
}

# US Sector ETFs (SPDR Sector Select)
SECTOR_ETFS: Dict[str, str] = {
    "XLF": "Financial",           # 金融
    "XLE": "Energy",              # エネルギー
    "XLK": "Technology",          # ハイテク
    "XLV": "Healthcare",          # ヘルスケア
    "XLP": "Consumer Staples",    # 生活必需品
    "XLI": "Industrials",         # 資本財
    "XLY": "Consumer Discretionary",  # 一般消費財
    "XLU": "Utilities",           # 公益
    "XLRE": "Real Estate",        # 不動産
}

# Sector names in Japanese
SECTOR_NAMES_JA: Dict[str, str] = {
    "XLF": "金融",
    "XLE": "エネルギー",
    "XLK": "ハイテク",
    "XLV": "ヘルスケア",
    "XLP": "生活必需品",
    "XLI": "資本財",
    "XLY": "一般消費財",
    "XLU": "公益",
    "XLRE": "不動産",
}

# Economic Cycle to Sector Mapping
CYCLE_SECTOR_MAP: Dict[str, List[str]] = {
    "early_recovery": ["XLF", "XLK", "XLRE"],  # 金融相場: 金融、ハイテク、不動産
    "expansion": ["XLI", "XLY", "XLE"],         # 業績相場: 資本財、一般消費財、エネルギー
    "early_recession": ["XLE", "XLP"],          # 逆金融相場: エネルギー、生活必需品
    "recession": ["XLU", "XLV", "XLP"],         # 逆業績相場: 公益、ヘルスケア、生活必需品
}

# Backtesting constants
BACKTEST_DEFAULT_INITIAL_CAPITAL = 1000000  # 100万円
BACKTEST_DEFAULT_POSITION_SIZE = 100  # 100株
BACKTEST_DEFAULT_COMMISSION_RATE = 0.005  # 0.5%
BACKTEST_DEFAULT_SLIPPAGE_RATE = 0.001  # 0.1%
BACKTEST_DEFAULT_STOP_LOSS_PCT = 0.05  # 5%
BACKTEST_DEFAULT_TAKE_PROFIT_PCT = 0.10  # 10%
BACKTEST_RETRAIN_PERIOD_DAYS = 30  # 30日ごとに再学習
BACKTEST_MIN_TRAINING_PERIOD_DAYS = 90  # 最소学習期間90日
