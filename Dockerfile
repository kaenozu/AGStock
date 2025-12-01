# ビルドステージ
FROM python:3.12-slim as builder

LABEL maintainer="AGStock Team"
LABEL description="AGStock - AI-Powered Multi-Asset Trading System"

WORKDIR /app

# システム依存関係のインストール
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Python依存関係のインストール
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --user -r requirements.txt

# 実行ステージ
FROM python:3.12-slim

WORKDIR /app

# 必要な実行時依存関係のみインストール
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ビルドステージからPythonパッケージをコピー
COPY --from=builder /root/.local /root/.local

# アプリケーションファイルのコピー
COPY . .

# データディレクトリ作成
RUN mkdir -p /app/data /app/logs

# 非rootユーザーで実行
RUN useradd -m -u 1000 agstock && \
    chown -R agstock:agstock /app
USER agstock

# PATHにユーザーのローカルbinを追加
ENV PATH=/root/.local/bin:$PATH

# ポート公開
EXPOSE 8503

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8503/_stcore/health || exit 1

# 起動コマンド
CMD ["streamlit", "run", "app.py", "--server.port=8503", "--server.address=0.0.0.0", "--server.headless=true"]
