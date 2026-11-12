"""AWF Guard: cli."""
from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from pathlib import Path
from typing import Sequence
import argparse
import json
import sys
from .atoms import AtomManifestIndex
from .command_receipts import CommandReceipt
from .ast_structure import audit_ast_pair_diff
from .static_audit import audit_ast_path
from .benchmark import audit_benchmark_directory
from .self_audit import audit_engine_self_hosting_integrity
from .command_receipts import run_and_record_command_receipt
from .claims import verify_agent_turn_claims


def _run_self_test() -> int:
    """Delegate to the modular 14-Slot self-test suite (positive checks + negative controls + dogfood audit)."""
    scripts_dir = str(Path(__file__).resolve().parent.parent)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    prev_dont_write = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        from awf_anti_goodhart_selftest_suite import run_comprehensive_54_gate_selftest
    finally:
        sys.dont_write_bytecode = prev_dont_write

    return run_comprehensive_54_gate_selftest()


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="AWF Guard: Universal 7-Gate x 14-Slot Anti-Goodhart & Self-Hosting Verification Engine (v3.7.0-rc.5)"
    )
    parser.add_argument("--self-test", action="store_true", help="Run built-in 14-Slot x 74-Subcheck positive self-test, negative controls, and Self-Hosting Dogfood audit")
    parser.add_argument("--audit-self", action="store_true", help="Run G6n Self-Hosting Zero-Violation Dogfood Audit on AWF Guard itself")
    parser.add_argument("--audit-ast", type=Path, help="Run static AST/dataflow/intent/tamper audit on a Python file or directory")
    parser.add_argument("--audit-ncc-tests", type=Path, help="Optional test file path to check NCC test-literal overlap with --audit-ast")
    parser.add_argument("--audit-pair", nargs=2, type=Path, metavar=("ORIG_PY", "GEN_PY"), help="Run Pair-Mode structural regression audit between original and generated Python files")
    parser.add_argument("--audit-benchmark", type=Path, help="Run BenchJack V1-V8 evaluator hackability & trust-boundary scan on a directory")
    parser.add_argument("--record-run", nargs=argparse.REMAINDER, help="Execute command and record a tamper-evident CommandReceipt")
    parser.add_argument("--receipt-ledger", type=Path, default=Path(".ag_receipts.json"), help="Path to CommandReceipt JSON ledger")
    parser.add_argument("--verify-claims", type=str, help="Verify an agent turn message against repo AST, git diff, and recorded receipts")
    parser.add_argument("--repo", type=Path, default=Path("."), help="Repository root for --verify-claims")
    parser.add_argument("--inspect-manifest", type=Path, help="Load and inspect an atom_manifest.json file")
    parser.add_argument("--trace-impact", type=str, help="Atom-ID to trace downstream DAG impact (used with --inspect-manifest)")
    args = parser.parse_args(argv)

    if args.audit_self:
        rep = audit_engine_self_hosting_integrity()
        print(json.dumps(rep, indent=2, ensure_ascii=False))
        return 0 if rep["status"] == "PASS" else 1

    if args.audit_benchmark is not None:
        rep = audit_benchmark_directory(args.audit_benchmark.expanduser().resolve())
        print(json.dumps(rep, indent=2, ensure_ascii=False))
        return 0 if rep["status"] == "PASS" else 1

    if args.record_run:
        cmd_list = [c for c in args.record_run if c != "--"]
        rec = run_and_record_command_receipt(cmd_list, receipt_ledger_path=args.receipt_ledger.expanduser().resolve())
        print(json.dumps(rec.to_dict(), indent=2, ensure_ascii=False))
        return 0 if rec.exit_code == 0 else rec.exit_code

    if args.verify_claims is not None:
        ledger_p = args.receipt_ledger.expanduser().resolve()
        loaded_receipts: List[CommandReceipt] = []
        if ledger_p.is_file():
            try:
                loaded_receipts = [CommandReceipt.from_dict(x) for x in json.loads(ledger_p.read_text(encoding="utf-8"))]
            except Exception:
                loaded_receipts = []
        rep = verify_agent_turn_claims(
            args.verify_claims,
            repo_root=args.repo.expanduser().resolve(),
            command_receipts=loaded_receipts,
        )
        print(json.dumps(rep, indent=2, ensure_ascii=False))
        return 0 if rep["status"] == "PASS" else 1

    if args.audit_pair is not None:
        orig_p, gen_p = args.audit_pair[0].expanduser().resolve(), args.audit_pair[1].expanduser().resolve()
        report = audit_ast_pair_diff(orig_p.read_text(encoding="utf-8"), gen_p.read_text(encoding="utf-8"))
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0 if report["status"] == "PASS" else 1

    if args.audit_ast is not None:
        ncc_p = args.audit_ncc_tests.expanduser().resolve() if args.audit_ncc_tests else None
        report = audit_ast_path(args.audit_ast.expanduser().resolve(), test_suite_path=ncc_p)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0 if report["status"] == "PASS" else 1

    if args.inspect_manifest is not None:
        manifest = AtomManifestIndex.load(args.inspect_manifest.expanduser().resolve())
        out: Dict[str, Any] = {
            "project": manifest.project_name,
            "atom_count": len(manifest.atoms),
            "atoms": list(manifest.atoms.keys()),
        }
        if args.trace_impact:
            out["modified_atom"] = args.trace_impact
            out["downstream_impact_dag"] = manifest.trace_downstream_impact(args.trace_impact)
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0

    return _run_self_test()
