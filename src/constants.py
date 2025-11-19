from typing import List, Dict

# List of Nikkei 225 Tickers (Simplified for initial version to ensure speed)
# In a real app, we might fetch this dynamically or have a fuller list.
# Adding .T for Yahoo Finance Japan compatibility.

NIKKEI_225_TICKERS: List[str] = [
    "7203.T", # Toyota
    "9984.T", # Softbank Group
    "6758.T", # Sony
    "6861.T", # Keyence
    "6098.T", # Recruit
    "8035.T", # Tokyo Electron
    "9983.T", # Fast Retailing
    "4063.T", # Shin-Etsu Chemical
    "9432.T", # NTT
    "7974.T", # Nintendo
    "8306.T", # MUFG
    "8316.T", # SMFG
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
    # Adding some popular ones for variety
    "5401.T", # Nippon Steel
    "7011.T", # Mitsubishi Heavy
    "9101.T", # NYK Line
    "9104.T", # Mitsui O.S.K.
    "9107.T", # Kawasaki Kisen
    "1605.T", # Inpex
    "5020.T", # ENEOS
    "8031.T", # Mitsui & Co
    "8002.T", # Marubeni
    "8591.T", # Orix
]

# Map for human readable names (Optional, but nice to have)
TICKER_NAMES: Dict[str, str] = {
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
