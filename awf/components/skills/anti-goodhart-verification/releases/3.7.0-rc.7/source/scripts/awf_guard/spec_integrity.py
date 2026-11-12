"""AWF Guard: spec integrity."""
from __future__ import annotations

from awf_guard_numeric_contracts import finite_array as _finite_array
from awf_guard_numeric_contracts import finite_call as _finite_call
from awf_guard_numeric_contracts import finite_float as _finite_float
from awf_guard_numeric_contracts import finite_inputs as _finite_inputs
import ast
import inspect
import numpy as np
from .station_spec import MetaBoundsPolicy
from .errors import SecondOrderCollusionError
from .station_spec import StationVerificationSpec
from .ast_utils import _ast_structure_similarity
from .ast_utils import _unwrap_target_fn
from .ast_utils import text_dedent


@_finite_inputs
def audit_spec_integrity(
    spec: StationVerificationSpec,
    policy: MetaBoundsPolicy = MetaBoundsPolicy(),
) -> None:
    """
    Second-Order Anti-Collusion Meta-Guard (`Meta-Guard`).
    Inspects `StationVerificationSpec` BEFORE running G1..G7 to ensure the spec itself was not watered down.
    """
    if spec.tier == 0:
        return

    max_lim_tol = (
        policy.max_allowed_limit_tol_stochastic
        if spec.mode == "stochastic"
        else policy.max_allowed_limit_tol_deterministic
    )
    if spec.limit_tol > max_lim_tol:
        raise SecondOrderCollusionError(
            f"[Meta-Guard Threshold Dilution] spec.limit_tol ({spec.limit_tol}) exceeds hard ceiling {max_lim_tol}."
        )

    if spec.tier >= 2:
        max_ora_tol = (
            policy.max_allowed_oracle_tol_stochastic
            if spec.mode == "stochastic"
            else policy.max_allowed_oracle_tol_deterministic
        )
        if spec.oracle_tol > max_ora_tol:
            raise SecondOrderCollusionError(
                f"[Meta-Guard Threshold Dilution] spec.oracle_tol ({spec.oracle_tol}) exceeds ceiling {max_ora_tol}."
            )
        if spec.min_perturbation_delta < policy.min_perturbation_floor:
            raise SecondOrderCollusionError(
                f"[Meta-Guard Sensitivity Dilution] spec.min_perturbation_delta ({spec.min_perturbation_delta}) "
                f"is below floor {policy.min_perturbation_floor}."
            )
        if spec.orthogonal_oracle_fn is None:
            raise SecondOrderCollusionError(
                "[Meta-Guard Missing Oracle] Tier-2 Production Seal requires a non-null `orthogonal_oracle_fn`."
            )
        raw_target = _finite_call(_unwrap_target_fn, spec.target_fn)
        raw_oracle = _finite_call(_unwrap_target_fn, spec.orthogonal_oracle_fn)
        if raw_oracle is raw_target:
            raise SecondOrderCollusionError(
                "[Meta-Guard Collusive Oracle] `orthogonal_oracle_fn` points to the exact same function as `target_fn`!"
            )
        try:
            src_target = inspect.getsource(raw_target)
            src_oracle = inspect.getsource(raw_oracle)
            if raw_target.__name__ in src_oracle and "def " in src_oracle:
                tree_ora = ast.parse(text_dedent(src_oracle))
                for node in ast.walk(tree_ora):
                    if isinstance(node, ast.Call) and getattr(node.func, "id", "") == raw_target.__name__:
                        raise SecondOrderCollusionError(
                            f"[Meta-Guard Collusive Oracle] `orthogonal_oracle_fn` directly calls `{raw_target.__name__}`!"
                        )
            ast_sim = _ast_structure_similarity(src_target, src_oracle)
            if ast_sim > policy.max_oracle_ast_similarity:
                raise SecondOrderCollusionError(
                    f"[Meta-Guard Collusive Copy-Paste Oracle] `orthogonal_oracle_fn` has AST similarity "
                    f"{ast_sim:.2f} > {policy.max_oracle_ast_similarity} with `target_fn`."
                )
        except (OSError, TypeError):
            src_target = ""

        if spec.symmetry_transform_fn is not None and spec.small_input_kwargs:
            sym_in = _finite_call(spec.symmetry_transform_fn, dict(spec.small_input_kwargs))
            diffs = []
            for k, v in spec.small_input_kwargs.items():
                if isinstance(v, np.ndarray) and k in sym_in:
                    diffs.append(_finite_float(np.linalg.norm(_finite_array(sym_in[k], dtype=float) - _finite_array(v, dtype=float))))
            if diffs and max(diffs) < 1e-8:
                raise SecondOrderCollusionError(
                    "[Meta-Guard Trivial Symmetry Spoofing] `symmetry_transform_fn` left all input arrays unchanged (Identity Map)!"
                )
