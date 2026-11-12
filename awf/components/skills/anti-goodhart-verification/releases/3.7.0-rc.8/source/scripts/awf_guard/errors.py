"""AWF Guard: errors."""
from __future__ import annotations




class SelfTestFailure(RuntimeError):
    """Raised by self-tests instead of `assert`, so checks survive `python -O`."""


class AntiGoodhartGateError(RuntimeError):
    """Raised when an operator, solver, or evaluator violates a First-Principles Anti-Goodhart Gate."""


class SecondOrderCollusionError(AntiGoodhartGateError):
    """Raised by Meta-Guard when a StationVerificationSpec attempts to dilute thresholds or spoof oracles."""


class AtomicContractViolationError(AntiGoodhartGateError):
    """Raised by `@scientific_atom` when cross-module shape, unit, domain, purity, dataflow, or intent contracts fail."""


class InformationBoundaryLeakError(AntiGoodhartGateError):
    """Raised when forbidden evaluation criteria, hold-out targets, or prompt context leak across agent boundaries."""


class BorderlineThresholdHuggingError(AntiGoodhartGateError):
    """Raised when `strict_reject_borderline=True` and an operator barely squeaks past a tolerance ceiling."""
