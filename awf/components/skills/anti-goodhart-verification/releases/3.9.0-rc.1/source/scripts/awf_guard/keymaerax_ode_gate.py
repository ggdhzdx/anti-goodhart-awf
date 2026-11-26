"""AWF Guard: KeYmaera X differential dynamic logic (dL) ODE invariant & Z3 non-vacuous precondition gate (`G5w`)."""
from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Any, Dict, List, Optional, Sequence, Tuple
import z3

from awf_guard_numeric_contracts import finite_float as _finite_float
from awf_guard_numeric_contracts import finite_inputs as _finite_inputs

_CLUSTER_JAVA_BIN = "/home/software/openjdk-21/bin/java"
_CLUSTER_KYX_JAR = "/home/software/keymaerax/keymaerax.jar"
_WARMED_KYX_CACHE_CANDIDATES = ("/home/zc/.keymaerax",)
_MIN_KYX_TIMEOUT_SEC = 5.0
_MAX_KYX_TIMEOUT_SEC = 180.0
_MIN_KYP_CERT_BYTES = 64
_TRIVIAL_POSTCONDITIONS = ("true", "1=1", "0=0", "1>=0", "0<=1")


def _extract_problem_body(kyx_code: str) -> str:
    match = re.search(r"\bProblem\b(.*?)\bEnd\s*\.", kyx_code, flags=re.DOTALL)
    return match.group(1).strip() if match else ""


def _verify_precondition_z3_sat(
    variables: Dict[str, str],
    assertions: Sequence[str],
) -> Tuple[bool, str]:
    if not variables or not assertions:
        return False, "precondition_variables and precondition_smt2_assertions must be non-empty"
    smt_lines: List[str] = []
    for var_name, sort_name in variables.items():
        if sort_name not in ("Real", "Int"):
            return False, f"Unsupported SMT sort `{sort_name}` for `{var_name}` (expected Real or Int)"
        smt_lines.append(f"(declare-const {var_name} {sort_name})")
    for expr in assertions:
        smt_lines.append(f"(assert {expr})")
    smt_text = "\n".join(smt_lines)
    try:
        parsed = z3.parse_smt2_string(smt_text)
        solver = z3.Solver()
        solver.add(parsed)
        verdict = solver.check()
        return verdict == z3.sat, str(verdict)
    except Exception as exc:
        return False, f"smt2_parse_error: {exc}"


def _prepare_isolated_kyx_home(tmp_root: Path) -> Path:
    local_home = tmp_root / "kyx_home"
    local_home.mkdir(parents=True, exist_ok=True)
    user_kyx = Path.home() / ".keymaerax"
    candidates = [user_kyx, *(Path(p) for p in _WARMED_KYX_CACHE_CANDIDATES)]
    for cand in candidates:
        if cand.is_dir() and (cand / "cache").is_dir():
            shutil.copytree(cand, local_home / ".keymaerax")
            break
    return local_home


def _build_kyx_command(local_home: Path, model_path: Path, cert_path: Path) -> Optional[List[str]]:
    if Path(_CLUSTER_JAVA_BIN).is_file() and Path(_CLUSTER_KYX_JAR).is_file():
        return [
            _CLUSTER_JAVA_BIN,
            f"-Duser.home={local_home}",
            "-Xss20M",
            "-da",
            "-jar",
            _CLUSTER_KYX_JAR,
            "-launch",
            "-prove",
            str(model_path),
            "-out",
            str(cert_path),
        ]
    kyx_bin = shutil.which("keymaerax")
    if kyx_bin is not None:
        return [kyx_bin, "-prove", str(model_path), "-out", str(cert_path)]
    return None


@_finite_inputs
def verify_keymaerax_ode_invariants(
    kyx_model_code: str,
    precondition_variables: Dict[str, str],
    precondition_smt2_assertions: Sequence[str],
    expected_postcondition_fragment: str,
    timeout_sec: float = 60.0,
) -> Dict[str, Any]:
    """
    KeYmaera X Differential Dynamic Logic (`dL`) Hybrid/ODE Invariant Proof & Z3 Non-Vacuous
    Precondition Satisfiability Gate (`G5w`).
    """
    t_out = _finite_float(timeout_sec)
    if not (_MIN_KYX_TIMEOUT_SEC <= t_out <= _MAX_KYX_TIMEOUT_SEC):
        raise ValueError(f"G5w timeout_sec must be in [{_MIN_KYX_TIMEOUT_SEC}, {_MAX_KYX_TIMEOUT_SEC}], got {t_out}")
    if not kyx_model_code.strip() or not expected_postcondition_fragment.strip():
        raise ValueError("G5w requires non-empty kyx_model_code and expected_postcondition_fragment")

    violations: List[str] = []
    problem_body = _extract_problem_body(kyx_model_code)
    if not problem_body or "->" not in problem_body or "[{" not in problem_body or "}]" not in problem_body:
        violations.append("KeYmaera X model must contain a `Problem ... -> [{ ODE }] Post End.` block.")
    else:
        antecedent, succedent = problem_body.split("->", 1)
        if re.search(r"\bfalse\b", antecedent, flags=re.IGNORECASE):
            violations.append("Vacuous `false` antecedent detected in KeYmaera X Problem precondition.")
        for var_name in precondition_variables:
            if not re.search(r"\b" + re.escape(var_name) + r"\b", antecedent):
                violations.append(
                    f"Declared Z3 precondition variable `{var_name}` is absent from `.kyx` Problem antecedent."
                )
        post_part = succedent.split("}]", 1)[1].strip()
        norm_post = re.sub(r"\s+", "", post_part).strip("()").lower()
        if norm_post in _TRIVIAL_POSTCONDITIONS:
            violations.append(f"Trivial tautological ODE postcondition `{post_part}` rejected.")
        if expected_postcondition_fragment.strip() not in post_part:
            violations.append(
                f"Expected postcondition fragment `{expected_postcondition_fragment.strip()}` missing from `{post_part}`."
            )

    precond_sat, z3_status = _verify_precondition_z3_sat(precondition_variables, precondition_smt2_assertions)
    if not precond_sat:
        violations.append(f"Vacuous or invalid ODE precondition rejected by Z3 (`{z3_status}`).")

    kyx_rc = -1
    proved = False
    cert_bytes = 0
    if not violations:
        with tempfile.TemporaryDirectory(prefix="ag_kyx_") as tmp_str:
            tmp_root = Path(tmp_str)
            local_home = _prepare_isolated_kyx_home(tmp_root)
            model_path = tmp_root / "ode_gate.kyx"
            cert_path = tmp_root / "ode_gate.kyp"
            model_path.write_text(kyx_model_code, encoding="utf-8")
            cmd = _build_kyx_command(local_home, model_path, cert_path)
            if cmd is None:
                violations.append("KeYmaera X prover (`keymaerax`) not found on host; G5w fails closed.")
            else:
                env = dict(os.environ)
                env["HOME"] = str(local_home)
                proc = subprocess.run(
                    cmd,
                    cwd=str(tmp_root),
                    env=env,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    timeout=t_out,
                    check=False,
                )
                kyx_rc = int(proc.returncode)
                stdout_text = proc.stdout or ""
                cert_bytes = int(cert_path.stat().st_size) if cert_path.is_file() else 0
                proved = (
                    kyx_rc == 0
                    and ("PROVED" in stdout_text)
                    and ("FAILED" not in stdout_text)
                    and (cert_bytes >= _MIN_KYP_CERT_BYTES)
                )
                if not proved:
                    tail = " | ".join(ln.strip() for ln in (stdout_text + "\n" + (proc.stderr or "")).splitlines()[-4:] if ln.strip())
                    violations.append(
                        f"KeYmaera X failed to prove ODE invariant (rc={kyx_rc}, cert_bytes={cert_bytes}): {tail[:240]}"
                    )

    return {
        "status": "PASS" if not violations else "FAIL",
        "precondition_satisfiable": precond_sat,
        "z3_precondition_status": z3_status,
        "keymaerax_returncode": kyx_rc,
        "proved": proved,
        "proof_certificate_bytes": cert_bytes,
        "violations": violations,
    }
