"""OpenTelemetry bootstrap (traces + metrics + logs) shared across services.

Env-driven via the standard OTEL_* variables. If OTEL_EXPORTER_OTLP_ENDPOINT is
unset this is a no-op, so tests and local runs without a collector stay clean.
Never emits secrets: only the standard instrumentation attributes are recorded.
"""

import logging
import os

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def init_telemetry(app, service_name: str, engine=None) -> bool:
    """Wire OTLP traces/metrics/logs and auto-instrument FastAPI (+ SQLAlchemy).

    Returns True if telemetry was enabled, False if it was skipped.
    """
    if not os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
        return False

    resource = Resource.create({"service.name": service_name})

    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(tracer_provider)

    metrics.set_meter_provider(
        MeterProvider(
            resource=resource,
            metric_readers=[PeriodicExportingMetricReader(OTLPMetricExporter())],
        )
    )

    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter()))
    logging.getLogger().addHandler(LoggingHandler(logger_provider=logger_provider))

    FastAPIInstrumentor.instrument_app(app)
    if engine is not None:
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

        SQLAlchemyInstrumentor().instrument(engine=engine)

    return True
