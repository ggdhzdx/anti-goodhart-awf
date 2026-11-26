"""AWF Guard: Lean 4 kernel proof, axiom-whitelist & non-vacuous inhabitation-witness gate (`G2c`)."""
from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Any, Callable, Dict, List, Optional, Sequence
import sympy as sp

from awf_guard_numeric_contracts import finite_call as _finite_call
from awf_guard_numeric_contracts import finite_float as _finite_float
from awf_guard_numeric_contracts import finite_inputs as _finite_inputs

_CLUSTER_LEAN_BIN = "/home/software/anaconda3/bin/lean"
_ALLOWED_STANDARD_LEAN_AXIOMS = frozenset({"propext", "Classical.choice", "Quot.sound"})
_FORBIDDEN_LEAN_DIRECTIVES = ("sorry", "admit", "axiom ", "unsafe ", "implemented_by", "@[extern")
_MAX_SYMPY_ORACLE_TOL = 1e-3
_MIN_TIMEOUT_SEC = 1.0
_MAX_TIMEOUT_SEC = 120.0
_SYMPY_EVAL_DIGITS = 35


def _strip_lean_comments(src: str) -> str:
    no_block = re.sub(r"/-.*?-/", " ", src, flags=re.DOTALL)
    no_line = re.sub(r"--[^\n]*", " ", no_block)
    return no_line


def _normalize_ws(text: str) -> str:
    return " ".join(text.split())


def _resolve_lean_binary() -> Optional[str]:
    if Path(_CLUSTER_LEAN_BIN).is_file():
        return _CLUSTER_LEAN_BIN
    return shutil.which("lean")


def _parse_printed_axioms(stdout_text: str, decl_name: str) -> Optional[List[str]]:
    does_not_depend = f"'{decl_name}' does not depend on any axioms"
    depends_prefix = f"'{decl_name}' depends on axioms:"
    for line in stdout_text.splitlines():
        stripped = line.strip()
        if stripped == does_not_depend:
            return []
        if stripped.startswith(depends_prefix):
            raw_list = stripped[len(depends_prefix):].strip().strip("[]")
            return [item.strip() for item in raw_list.split(",") if item.strip()]
    return None


@_finite_inputs
def verify_lean4_symbolic_proof_and_inhabitation(
    lean_source_code: str,
    theorem_name: str,
    expected_theorem_signature: str,
    inhabitation_witness_name: str,
    sympy_expr_str: Optional[str] = None,
    target_fn: Optional[Callable[..., Any]] = None,
    sample_points: Optional[Sequence[Dict[str, float]]] = None,
    oracle_tol: float = 1e-8,
    timeout_sec: float = 30.0,
) -> Dict[str, Any]:
    """
    Lean 4 Formal Kernel Proof, Standard-Axiom Whitelist, Non-Vacuous Hypothesis Inhabitation Witness,
    and SymPy Symbolic-to-Numeric Equivalence Gate (`G2c`).
    """
    tol_f = _finite_float(oracle_tol)
    t_out = _finite_float(timeout_sec)
    if not (0.0 < tol_f <= _MAX_SYMPY_ORACLE_TOL) or not (_MIN_TIMEOUT_SEC <= t_out <= _MAX_TIMEOUT_SEC):
        raise ValueError(f"G2c invalid bounds: oracle_tol={tol_f}, timeout_sec={t_out}")
    if not lean_source_code.strip() or not theorem_name.strip() or not expected_theorem_signature.strip() or not inhabitation_witness_name.strip():
        raise ValueError("G2c requires non-empty lean_source_code, theorem_name, expected_theorem_signature, and inhabitation_witness_name")
    if theorem_name.strip() == inhabitation_witness_name.strip():
        raise ValueError("inhabitation_witness_name must be distinct from theorem_name")

    violations: List[str] = []
    stripped = _strip_lean_comments(lean_source_code)
    norm_src = _normalize_ws(stripped)
    norm_sig = _normalize_ws(expected_theorem_signature)

    for token in _FORBIDDEN_LEAN_DIRECTIVES:
        if re.search(r"\b" + re.escape(token.strip()) + r"\b", stripped) if token.isalpha() else (token in stripped):
            violations.append(f"Forbidden Lean bypass token `{token.strip()}` detected in source.")

    if norm_sig not in norm_src:
        violations.append(
            f"Expected theorem signature `{norm_sig}` not found verbatim in comment-stripped Lean source."
        )

    witness_pat = re.compile(
        r"\b(?:theorem|lemma|def)\s+" + re.escape(inhabitation_witness_name.strip()) + r"\b([^:=]*):",
        flags=re.DOTALL,
    )
    if not witness_pat.search(stripped) or ("∃" not in stripped and "Exists" not in stripped):
        violations.append(
            f"Non-vacuous existential inhabitation witness `{inhabitation_witness_name}` (`∃ ...`) missing."
        )
    if re.search(r":\s*False\s*->", stripped) or re.search(r"\(\s*_\s*:\s*False\s*\)", stripped):
        violations.append("Contradictory `False` premise detected (vacuous truth bypass).")

    lean_bin = _resolve_lean_binary()
    theorem_axioms: List[str] = []
    witness_axioms: List[str] = []
    lean_rc = -1

    if lean_bin is None:
        violations.append("Lean 4 compiler binary (`lean`) not found on host; G2c fails closed.")
    elif not violations:
        harness_src = (
            lean_source_code.rstrip()
            + f"\n#print axioms {theorem_name.strip()}\n"
            + f"#print axioms {inhabitation_witness_name.strip()}\n"
        )
        with tempfile.TemporaryDirectory(prefix="ag_lean4_") as tmp_dir:
            lean_file = Path(tmp_dir) / "VerifyGate.lean"
            lean_file.write_text(harness_src, encoding="utf-8")
            env = dict(os.environ)
            proc = subprocess.run(
                [lean_bin, str(lean_file)],
                cwd=tmp_dir,
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=t_out,
                check=False,
            )
            lean_rc = int(proc.returncode)
            combined_out = (proc.stdout or "") + "\n" + (proc.stderr or "")
            if lean_rc != 0:
                violations.append(f"Lean 4 kernel rejected proof (rc={lean_rc}): {combined_out.strip()[:240]}")
            if "uses 'sorry'" in combined_out or "declaration uses 'sorry'" in combined_out:
                violations.append("Lean 4 reported `sorryAx` contamination in compiled declaration.")

            parsed_thm = _parse_printed_axioms(combined_out, theorem_name.strip())
            parsed_wit = _parse_printed_axioms(combined_out, inhabitation_witness_name.strip())
            if parsed_thm is None or parsed_wit is None:
                violations.append("Failed to parse `#print axioms` output for theorem or inhabitation witness.")
            else:
                theorem_axioms = parsed_thm
                witness_axioms = parsed_wit
                disallowed = sorted((set(theorem_axioms) | set(witness_axioms)) - _ALLOWED_STANDARD_LEAN_AXIOMS)
                if disallowed:
                    violations.append(f"Disallowed axioms used in Lean proof: {disallowed}")

    sympy_checked = 0
    max_sympy_err = 0.0
    if (sympy_expr_str is not None) or (target_fn is not None) or (sample_points is not None):
        if not sympy_expr_str or target_fn is None or not sample_points:
            violations.append("sympy_expr_str, target_fn, and non-empty sample_points must be provided together.")
        else:
            sym_expr = sp.sympify(sympy_expr_str)
            for pt in sample_points:
                subs_map = {sp.Symbol(k): sp.Float(str(_finite_float(v)), _SYMPY_EVAL_DIGITS) for k, v in pt.items()}
                ref_val = _finite_float(float(sym_expr.evalf(_SYMPY_EVAL_DIGITS, subs=subs_map)))
                cand_val = _finite_float(_finite_call(target_fn, **pt))
                err = abs(cand_val - ref_val)
                if err > max_sympy_err:
                    max_sympy_err = err
                sympy_checked += 1
            if max_sympy_err > tol_f:
                violations.append(
                    f"Python operator deviates from SymPy symbolic oracle `{sympy_expr_str}`: "
                    f"max_err={max_sympy_err:.3e} > {tol_f:.3e}"
                )

    return {
        "status": "PASS" if not violations else "FAIL",
        "theorem_name": theorem_name.strip(),
        "inhabitation_witness_name": inhabitation_witness_name.strip(),
        "lean_returncode": lean_rc,
        "theorem_axioms": theorem_axioms,
        "witness_axioms": witness_axioms,
        "sympy_points_checked": sympy_checked,
        "max_sympy_oracle_err": round(max_sympy_err, 14),
        "oracle_tolerance": tol_f,
        "violations": violations,
    }
