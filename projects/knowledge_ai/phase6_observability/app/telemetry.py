"""
Phase 6: 可観測性の3本柱を FastAPI に組み込む
================================================
  1. メトリクス  → Prometheus（カウンター・ヒストグラム）
  2. ログ       → 構造化JSON（CloudWatch/ELKに流す）
  3. トレース    → OpenTelemetry（リクエストの処理経路を追跡）

考えてほしい疑問:
  Q1. リクエスト数・エラー率・レイテンシの3つが「黄金シグナル」と呼ばれる理由は？
  Q2. SLI「99%のリクエストが200ms以内に返る」をPrometheusクエリで表現するには？
      ヒント: histogram_quantile(0.99, ...)
  Q3. 分散トレーシングを使わないと、マイクロサービス間の問題がなぜ見えないのか？

main.py に追加するコード:
  from phase6_observability.app.telemetry import setup_telemetry
  setup_telemetry(app)
"""

import json
import logging
import time
from collections.abc import Callable

from fastapi import FastAPI, Request, Response
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST


# --- Prometheus メトリクス定義 ---

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],  # ラベルで絞り込みが可能になる
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    # バケット: SLOのしきい値を含める（0.1秒・0.5秒・1秒・2秒）
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0],
)

# [実装してみよう] LLM APIコールの所要時間を計測するヒストグラムを追加する
LLM_CALL_DURATION = Histogram(
    "llm_call_duration_seconds",
    "LLM API call duration in seconds",
    ["model"],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
)


# --- 構造化ログ設定 ---

class StructuredLogger(logging.Formatter):
    """JSON形式のログ出力（CloudWatch/ELKでフィルタリングしやすい）"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }
        if hasattr(record, "trace_id"):
            log_data["trace_id"] = record.trace_id  # トレースIDをログに含める
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data, ensure_ascii=False)


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("knowledge_ai")
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredLogger())
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


# --- OpenTelemetry トレーシング設定 ---

def setup_tracing(service_name: str = "knowledge-ai-api") -> None:
    """
    OpenTelemetry によるトレーシングのセットアップ。
    JaegerやDatadogなどのバックエンドにスパンを送信する。
    """
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)

    # OTLP Exporter（Jaeger/Grafana Tempoに送信）
    exporter = OTLPSpanExporter(endpoint="http://jaeger:4317", insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))

    trace.set_tracer_provider(provider)


# --- FastAPI ミドルウェア ---

def setup_telemetry(app: FastAPI) -> None:
    """可観測性のすべての設定を一括でアプリに追加する"""
    logger = setup_logging()
    setup_tracing()

    # FastAPI の自動計装（リクエスト/レスポンスのスパン自動生成）
    FastAPIInstrumentor.instrument_app(app)
    # SQLAlchemy の自動計装（クエリのスパン自動生成）
    SQLAlchemyInstrumentor().instrument()

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next: Callable) -> Response:
        """
        リクエストごとにPrometheusメトリクスを記録するミドルウェア。

        [考える] ミドルウェアでの処理はすべてのリクエストに適用される。
        重い処理をここに入れるとAPIパフォーマンスに影響する。
        """
        start_time = time.time()

        response = await call_next(request)

        duration = time.time() - start_time
        endpoint = request.url.path

        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=response.status_code,
        ).inc()

        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=endpoint,
        ).observe(duration)

        # 遅いリクエストを警告ログに出力
        if duration > 2.0:
            logger.warning(
                f"Slow request: {request.method} {endpoint} took {duration:.2f}s",
                extra={"duration": duration, "endpoint": endpoint},
            )

        return response

    @app.get("/metrics")
    async def metrics():
        """Prometheusがスクレイプするエンドポイント"""
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
