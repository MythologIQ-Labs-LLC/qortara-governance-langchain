"""OTel traceparent propagation — LangSmith trace correlation."""

from __future__ import annotations

import pytest

from qortara_governance.otel import current_trace_context, tag_evidence_id


def test_current_trace_context_returns_none_without_active_span() -> None:
    """Outside an active OTel span, returns None (not a malformed TraceContext)."""
    # OpenTelemetry default NoOpTracer produces invalid spans; our code
    # correctly returns None when span_ctx.is_valid is False.
    ctx = current_trace_context()
    assert ctx is None


def test_current_trace_context_within_active_span() -> None:
    """Inside an active span, returns valid W3C traceparent."""
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
    except ImportError:
        pytest.skip("opentelemetry-sdk not installed")

    # Stand up a minimal TracerProvider so spans are actually valid.
    prev = trace.get_tracer_provider()
    provider = TracerProvider()
    trace.set_tracer_provider(provider)
    tracer = provider.get_tracer("qortara-test")

    try:
        with tracer.start_as_current_span("test-span"):
            ctx = current_trace_context()
            assert ctx is not None
            # Format: 00-<32hex>-<16hex>-<2hex>
            parts = ctx.traceparent.split("-")
            assert len(parts) == 4
            assert parts[0] == "00"
            assert len(parts[1]) == 32
            assert len(parts[2]) == 16
            assert len(parts[3]) == 2
    finally:
        trace.set_tracer_provider(prev)  # type: ignore[arg-type]


def test_tag_evidence_id_sets_span_attribute() -> None:
    """tag_evidence_id attaches qortara.evidence_id to the current span."""
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
    except ImportError:
        pytest.skip("opentelemetry-sdk not installed")

    prev = trace.get_tracer_provider()
    provider = TracerProvider()
    trace.set_tracer_provider(provider)
    tracer = provider.get_tracer("qortara-test")

    try:
        with tracer.start_as_current_span("test-span") as span:
            tag_evidence_id("evidence-abc-123")
            # Span's attributes should now include qortara.evidence_id.
            assert span.attributes.get("qortara.evidence_id") == "evidence-abc-123"
    finally:
        trace.set_tracer_provider(prev)  # type: ignore[arg-type]
