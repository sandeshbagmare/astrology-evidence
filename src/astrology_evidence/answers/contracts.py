"""Small provider contracts; callers supply only minimized, authorized input."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GenerationRequest:
    prompt: str
    timeout_seconds: float = 120
    max_output_tokens: int = 1800


@dataclass(frozen=True)
class GenerationResult:
    content: str
    usage: dict[str, int] | None = None
    model: str = "gpt-6.1-sol"


class ProviderError(Exception):
    """Safe public failure. Never attach the upstream body or exception."""

    def __init__(self, code: str, *, unknown: bool = False) -> None:
        super().__init__(code)
        self.code = code
        self.unknown = unknown
