"""Shared, deliberately un-fused forensic result types."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

Status = Literal["detected", "not_detected", "unavailable", "error"]


@dataclass
class ForensicResult:
    scheme: str
    status: Status
    asset: str
    summary: str
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)