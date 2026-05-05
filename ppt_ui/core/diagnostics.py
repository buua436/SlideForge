from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


DiagnosticLevel = Literal["error", "warning", "info"]


@dataclass(frozen=True)
class Diagnostic:
    """Structured parse/render feedback for agent-facing workflows."""

    level: DiagnosticLevel
    code: str
    message: str
    path: str = "$"
    suggestion: str | None = None


class DiagnosticError(ValueError):
    """Raised when diagnostics contain blocking errors."""

    def __init__(self, diagnostics: list[Diagnostic]) -> None:
        self.diagnostics = diagnostics
        first = diagnostics[0] if diagnostics else None
        message = first.message if first is not None else "SlideForge validation failed"
        super().__init__(message)


@dataclass
class DiagnosticBag:
    """Mutable collector used by parsers and renderers."""

    items: list[Diagnostic] = field(default_factory=list)

    def add(
        self,
        level: DiagnosticLevel,
        code: str,
        message: str,
        *,
        path: str = "$",
        suggestion: str | None = None,
    ) -> None:
        self.items.append(Diagnostic(level=level, code=code, message=message, path=path, suggestion=suggestion))

    def error(self, code: str, message: str, *, path: str = "$", suggestion: str | None = None) -> None:
        self.add("error", code, message, path=path, suggestion=suggestion)

    def warning(self, code: str, message: str, *, path: str = "$", suggestion: str | None = None) -> None:
        self.add("warning", code, message, path=path, suggestion=suggestion)

    def info(self, code: str, message: str, *, path: str = "$", suggestion: str | None = None) -> None:
        self.add("info", code, message, path=path, suggestion=suggestion)

    @property
    def has_errors(self) -> bool:
        return any(item.level == "error" for item in self.items)

    def raise_for_errors(self) -> None:
        errors = [item for item in self.items if item.level == "error"]
        if errors:
            raise DiagnosticError(errors)
