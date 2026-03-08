# Phase 3: マルチステージビルドによる最適化されたDockerfile
# ============================================================
# 学習ポイント:
#   - マルチステージビルドで本番イメージを最小化する
#   - 非rootユーザーで実行してセキュリティを高める
#   - レイヤーキャッシュを意識した命令の順序
#
# 考えてほしい疑問:
#   Q1. なぜ requirements.txt を COPY した後に CMD でなく RUN pip install するのか？
#       （ヒント: Dockerのレイヤーキャッシュ）
#   Q2. COPY . . を最後にしている理由は？
#   Q3. 非rootユーザーで動かす理由は？root で動かすと何のリスクがあるか？
#   Q4. このイメージのサイズを計測して、python:3.11 ベースと python:3.11-slim の差を比較する

# --- ステージ1: 依存関係のインストール ---
FROM python:3.11-slim AS builder

WORKDIR /app

# 依存ライブラリだけ先にコピー（キャッシュ効率化）
# ソースコードを変更しても、requirements.txtが変わらなければこの層は再利用される
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# --- ステージ2: 本番イメージ ---
FROM python:3.11-slim AS production

# セキュリティ: 非rootユーザーを作成して実行
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# builderからインストール済みパッケージだけコピー（開発ツールを含まない）
COPY --from=builder /root/.local /home/appuser/.local

# アプリコードをコピー（最後にすることでキャッシュを最大活用）
COPY --chown=appuser:appuser phase1_api/ ./
COPY --chown=appuser:appuser phase2_ai/ ./phase2_ai/

USER appuser

ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

# [考える] CMD と ENTRYPOINT の違いは何か？
# CMD: docker run 時に上書き可能 → 開発時に便利
# ENTRYPOINT: 上書きしにくい → 本番用コマンドの固定に使う
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
