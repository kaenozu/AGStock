# """
# フォーマッターユーティリティ
# 数値、通貨、パーセンテージなどの統一されたフォーマット関数
from typing import Optional
import pandas as pd
# """
def format_currency(value: Optional[float], symbol: str = "¥", decimals: int = 0, show_sign: bool = False) -> str:
    pass
#     """
#     通貨フォーマット（統一フォーマット）
#         Args:
    pass
#             value: 金額
#         symbol: 通貨記号
#         decimals: 小数点以下の桁数
#         Returns:
    pass
#             フォーマット済み文字列（例: "¥1,234,567"）
#         if value is None or pd.isna(value):
    pass
#             return "N/A"
#         if decimals == 0:
    pass
#             formatted = f"{value:,.0f}"
#     else:
    pass
#         formatted = f"{value:,.{decimals}f}"
#         if show_sign:
    pass
#             sign = "+" if value >= 0 else ""
#         return f"{sign}{symbol}{formatted}" if value >= 0 else f"{symbol}{formatted}"
#         return f"{symbol}{formatted}"
# """
def format_currency_jp(value: Optional[float]) -> str:
#     """日本円を万/億単位で見やすく整形。"""
if value is None or pd.isna(value):
        return "N/A"
        if value >= 100_000_000:
            return f"¥{value/100_000_000:.2f}億"
    if value >= 10_000:
        return f"¥{value/10_000:.1f}万"
    return f"¥{value:,.0f}"
def format_percentage(value: Optional[float], decimals: int = 2, show_sign: bool = False) -> str:
    pass
#     """
#     パーセンテージフォーマット
#         Args:
    pass
#             value: 値（0.05 = 5%）
#         decimals: 小数点以下の桁数
#         show_sign: 符号を常に表示するか
#         Returns:
    pass
#             フォーマット済み文字列（例: "+5.00%" or "5.00%"）
#         if value is None or pd.isna(value):
    pass
#             return "N/A"
#         pct_value = value * 100
#     if show_sign:
    pass
#         return f"{pct_value:+.{decimals}f}%"
#     else:
    pass
#         return f"{pct_value:.{decimals}f}%"
# """
def format_number(value: Optional[float], decimals: int = 2, suffix: str = "") -> str:
    pass
#     """
#     数値フォーマット
#         Args:
    pass
#             value: 数値
#         decimals: 小数点以下の桁数
#         suffix: 接尾辞（例: "倍", "x"）
#         Returns:
    pass
#             フォーマット済み文字列
#         if value is None or pd.isna(value):
    pass
#             return "N/A"
#         formatted = f"{value:,.{decimals}f}"
#     return f"{formatted}{suffix}" if suffix else formatted
# """
def format_large_number(value: Optional[float], decimals: int = 1) -> str:
    pass
#     """
#     大きな数値を読みやすく（K, M, B表記）
#         Args:
    pass
#             value: 数値
#         decimals: 小数点以下の桁数
#         Returns:
    pass
#             フォーマット済み文字列（例: "1.5M", "3.2B"）
#         if value is None or pd.isna(value):
    pass
#             return "N/A"
#         abs_value = abs(value)
#     sign = "-" if value < 0 else ""
#         if abs_value >= 1_000_000_000:  # Billion
#         return f"{sign}{abs_value / 1_000_000_000:.{decimals}f}B"
#     elif abs_value >= 1_000_000:  # Million
#         return f"{sign}{abs_value / 1_000_000:.{decimals}f}M"
#     elif abs_value >= 1_000:  # Thousand
#         return f"{sign}{abs_value / 1_000:.{decimals}f}K"
#     else:
    pass
#         # テストでは小数点以下を切り捨て気味に扱うため、floorベースで丸める
#         factor = 10**decimals
#         trimmed = int(abs_value * factor) / factor
#         return f"{sign}{trimmed:.{decimals}f}"
# """
def format_date(date, format_str: str = "%Y-%m-%d") -> str:
    pass
#     """
#     日付フォーマット
#         Args:
    pass
#             date: 日付オブジェクト
#         format_str: フォーマット文字列
#         Returns:
    pass
#             フォーマット済み日付文字列
#         if date is None or pd.isna(date):
    pass
#             return "N/A"
#         try:
    pass
#             if hasattr(date, "strftime"):
    pass
#                 return date.strftime(format_str)
#         else:
    pass
#             return pd.to_datetime(date).strftime(format_str)
#     except Exception:
    pass
#         return str(date)
# """
def get_risk_level(max_drawdown: float) -> str:
    pass
#     """
#     ドローダウンからリスクレベルを判定
#         Args:
    pass
#             max_drawdown: 最大ドローダウン（負の値）
#         Returns:
    pass
#             リスクレベル文字列: "low", "medium", "high"
#         mdd = abs(max_drawdown)
#         if mdd < 0.1:
    pass
#             return "low"
#     elif mdd < 0.2:
    pass
#         return "medium"
#     else:
    pass
#         return "high"
# """
def get_sentiment_label(score: float) -> str:
    pass
#     """
#     センチメントスコアからラベルを判定
#         Args:
    pass
#             score: センチメントスコア（-1 ~ 1）
#         Returns:
    pass
#             センチメントラベル: "Positive", "Neutral", "Negative"
#         if score >= 0.15:
    pass
#             return "Positive"
#     elif score <= -0.15:
    pass
#         return "Negative"
#     else:
    pass
#         return "Neutral"
# """
def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    pass
#     """
#     テキストを指定長で切り詰め
#         Args:
    pass
#             text: 元のテキスト
#         max_length: 最大長
#         suffix: 切り詰め時の接尾辞
#         Returns:
    pass
#             切り詰められたテキスト
#         if text is None:
    pass
#             return ""
#         if len(text) <= max_length:
    pass
#             return text
#     else:
    pass
#         return text[: max_length - len(suffix)] + suffix
# # DataFrameのスタイリング用ヘルパー
# """
def style_dataframe_currency(df: pd.DataFrame, columns: list, symbol: str = "¥") -> pd.DataFrame:
    pass
#     """
#     DataFrameの通貨カラムをフォーマット
#         Args:
    pass
#             df: DataFrame
#         columns: フォーマット対象のカラム名リスト
#         symbol: 通貨記号
#         Returns:
    pass
#             スタイル適用済みDataFrame
#         styled_df = df.copy()
#     for col in columns:
    pass
#         if col in styled_df.columns:
    pass
#             styled_df[col] = styled_df[col].apply(lambda x: format_currency(x, symbol=symbol))
#     return styled_df
# """
def style_dataframe_percentage(
        df: pd.DataFrame, columns: list, decimals: int = 2, show_sign: bool = False
# """
# ) -> pd.DataFrame:
#     """
DataFrameのパーセンテージカラムをフォーマット
        Args:
            df: DataFrame
        columns: フォーマット対象のカラム名リスト
        decimals: 小数点以下桁数
        show_sign: 符号表示
        styled_df = df.copy()
    for col in columns:
        if col in styled_df.columns:
            styled_df[col] = styled_df[col].apply(
                lambda x: format_percentage(x, decimals=decimals, show_sign=show_sign)
            )
    return styled_df
# """
def style_dataframe_percentage(df: pd.DataFrame, columns: list, decimals: int = 2) -> pd.DataFrame:
    pass
#     """
#     DataFrameのパーセンテージカラムをフォーマット
#         Args:
    pass
#             df: DataFrame
#         columns: フォーマット対象のカラム名リスト
#         decimals: 小数点以下の桁数
#         Returns:
    pass
#             スタイル適用済みDataFrame
#         styled_df = df.copy()
#     for col in columns:
    pass
#         if col in styled_df.columns:
    pass
#             styled_df[col] = styled_df[col].apply(lambda x: format_percentage(x, decimals=decimals))
#     return styled_df
# """
