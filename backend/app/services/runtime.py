"""Runtime helpers for demo, local LLM, and hosted-agent operation."""

from contextlib import contextmanager
from contextvars import ContextVar
from collections.abc import Iterator

from app.config import settings

_ALLOWED_MODES = {"demo", "llm", "hosted", "auto"}
_runtime_override: ContextVar[str | None] = ContextVar("runtime_mode_override", default=None)


def _normalise_mode(mode: str | None, default: str = "demo") -> str:
    configured = (mode or default).strip().lower()
    return configured if configured in _ALLOWED_MODES else default


@contextmanager
def runtime_mode_override(mode: str | None) -> Iterator[None]:
    """Temporarily override runtime mode for one request task."""
    normalised = _normalise_mode(mode, default="") if mode else None
    token = _runtime_override.set(normalised)
    try:
        yield
    finally:
        _runtime_override.reset(token)


def get_runtime_mode() -> str:
    """Return the effective runtime mode."""
    override = _runtime_override.get()
    if override:
        configured = override
    else:
        configured = _normalise_mode(settings.RUNTIME_MODE, default="demo")

    if configured != "auto":
        return configured

    if settings.LOCAL_LLM_MODE:
        return "llm"
    if settings.DEMO_MODE:
        return "demo"
    return "hosted"


def use_demo_mode() -> bool:
    return get_runtime_mode() == "demo"


def use_llm_mode() -> bool:
    return get_runtime_mode() == "llm"


def use_hosted_mode() -> bool:
    return get_runtime_mode() == "hosted"
