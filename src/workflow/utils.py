"""Shared utilities for pipeline nodes."""
from langgraph.config import get_stream_writer


def get_writer():
    """Return stream writer, or no-op if outside runnable context.

    get_stream_writer() raises RuntimeError when called outside
    a running graph (e.g. in unit tests). This wrapper returns a
    silent no-op instead.
    """
    try:
        return get_stream_writer()
    except RuntimeError:
        return lambda x: None
