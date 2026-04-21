"""OTel W3C traceparent extraction + qortara.evidence_id span attribute.

Provides LangSmith trace-viewer alignment: Qortara evidence records share
trace IDs with LangSmith spans via standard W3C Trace Context propagation.
"""

from __future__ import annotations

from qortara_protocol.action import TraceContext

try:
    from opentelemetry import trace

    _HAS_OTEL = True
except ImportError:  # pragma: no cover
    _HAS_OTEL = False


def current_trace_context() -> TraceContext | None:
    """Return current OTel span's traceparent, or None if no active span."""
    if not _HAS_OTEL:
        return None
    span = trace.get_current_span()
    span_ctx = span.get_span_context()
    if not span_ctx.is_valid:
        return None
    # Format: 00-<trace_id>-<span_id>-<flags> per W3C Trace Context.
    traceparent = (
        f"00-{format(span_ctx.trace_id, '032x')}"
        f"-{format(span_ctx.span_id, '016x')}"
        f"-{format(span_ctx.trace_flags, '02x')}"
    )
    return TraceContext(traceparent=traceparent, tracestate=None)


def tag_evidence_id(evidence_id: str) -> None:
    """Attach evidence_id as a span attribute on the current span.

    LangSmith's trace viewer surfaces span attributes, so Qortara evidence
    records become findable from LangSmith-rendered traces.
    """
    if not _HAS_OTEL:
        return
    span = trace.get_current_span()
    if span.is_recording():
        span.set_attribute("qortara.evidence_id", evidence_id)
