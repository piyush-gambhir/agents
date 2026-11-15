import anthropic

CACHE_CONTROL_EPHEMERAL = anthropic.types.CacheControlEphemeralParam(type="ephemeral")

__all__ = ["CACHE_CONTROL_EPHEMERAL"]
