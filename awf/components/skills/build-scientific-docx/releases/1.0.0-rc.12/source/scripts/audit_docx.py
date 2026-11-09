#!/usr/bin/env python3
"""Audit DOCX package integrity, native equations, unclipped layout, zero residual LaTeX/Markdown/work-codes, and media deltas."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import zipfile

from docx import Document
from lxml import etree


NAMESPACES = {
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
}

OMML_PLACEHOLDER_STRIP_RE = re.compile(r"\{\{OMML(?:_INLINE)?:\s*(?:(?!\{\{OMML).)*?\}\}+")

RESIDUAL_LATEX_RE = re.compile(
    r"(?:"
    r"\$"
    r"|\\(?:mathrm|mathit|mathbf|mathcal|text|textbf|textit|operatorname|frac|dfrac|tfrac|sqrt"
    r"|sum|prod|int|left|right|middle|hat|bar|overline|tilde|vec|dot|ddot"
    r"|alpha|beta|gamma|delta|epsilon|varepsilon|zeta|eta|theta|vartheta|iota|kappa|lambda|mu|nu|xi|pi|rho|sigma|tau|upsilon|phi|varphi|chi|psi|omega"
    r"|Gamma|Delta|Theta|Lambda|Xi|Pi|Sigma|Phi|Psi|Omega"
    r"|cdot|times|pm|mp|le|leq|ge|geq|neq|ne|approx|sim|propto|equiv|gg|ll|in|notin|subset|supset"
    r"|partial|nabla|infty|hbar|ddagger|dagger|permil|perp|parallel|forall|exists|AA|circ|degree|bullet|oplus|ominus|dots|ldots|cdots"
    r"|to|gets|rightarrow|leftarrow|leftrightarrow|Rightarrow|Leftarrow|rightleftharpoons|leftrightharpoons"
    r"|langle|rangle|lbrace|rbrace|vert|Vert|lvert|rvert|lVert|rVert|quad|qquad)\b"
    r"|^#{1,6}\s"
    r"|\*\*"
    r")"
)

RESIDUAL_WORK_CODE_RE = re.compile(
    r"(?:PPT\s*第\s*\d+\s*页|\bSlide\s+\d+\b|完全拉平起点|拉平起点|completely leveled starting point|补跑了|重跑了|临时脚本|\bTODO\b|\bFIXME\b)"
)

RESIDUAL_EXAGGERATION_RE = re.compile(
    r"(?:"
    r"从根本上"
    r"|三支柱|三大[^\n，。；]{0,6}支柱|第[一二三]动力学支柱|动力学支柱[一二三]|支柱[一二三]"
    r"|彻底(?:消除|打通|解决|克服|截断|失活|杜绝|根除|摆脱|阻断)"
    r"|完全(?:囚禁|锁定|死锁)"
    r"|全面超越|超长循环|极具应用前景"
    r"|无可争辩|毋庸置疑|毫无疑问"
    r")"
)

RESIDUAL_TEMPLATE_PLACEHOLDER_RE = re.compile(
    r"(?:"
    r"\b[xX]{5,}\b"
    r"|Insert\s+text\s+for\s+Table\s+of\s+Contents\s+here"
    r"|\(\(\s*Maximum\s+\d+\s+characters"
    r"|\[Insert\s+[^\]]+\s+here\]"
    r"|Author\s+1,\*\s+Author\s+2"
    r")",
    re.IGNORECASE,
)


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _scan_text_blocks(document) -> tuple[int, int, list[str], int, list[str], int, list[str], int, list[str]]:
    """Scan all body paragraphs and unique table cells for residual placeholders, LaTeX/Markdown tokens, work codes, exaggerated claims, and publisher template placeholders."""
    residual_omml = 0
    residual_latex = 0
    residual_latex_examples: list[str] = []
    residual_work_codes = 0
    residual_work_code_examples: list[str] = []
    residual_exaggerations = 0
    residual_exaggeration_examples: list[str] = []
    residual_template_placeholders = 0
    residual_template_placeholder_examples: list[str] = []

    def check_text(coord: str, text: str) -> None:
        nonlocal residual_omml, residual_latex, residual_work_codes, residual_exaggerations, residual_template_placeholders
        if "{{OMML" in text:
            residual_omml += 1
        cleaned = OMML_PLACEHOLDER_STRIP_RE.sub("", text)
        m_latex = RESIDUAL_LATEX_RE.search(cleaned)
        if m_latex:
            residual_latex += 1
            if len(residual_latex_examples) < 20:
                snippet = cleaned.strip()
                if len(snippet) > 80:
                    snippet = snippet[:77] + "..."
                residual_latex_examples.append(f"{coord} ({m_latex.group(0)}): {snippet}")
        m_code = RESIDUAL_WORK_CODE_RE.search(cleaned)
        if m_code:
            residual_work_codes += 1
            if len(residual_work_code_examples) < 20:
                snippet = cleaned.strip()
                if len(snippet) > 80:
                    snippet = snippet[:77] + "..."
                residual_work_code_examples.append(f"{coord} ({m_code.group(0)}): {snippet}")
        m_exag = RESIDUAL_EXAGGERATION_RE.search(cleaned)
        if m_exag:
            residual_exaggerations += 1
            if len(residual_exaggeration_examples) < 20:
                snippet = cleaned.strip()
                if len(snippet) > 80:
                    snippet = snippet[:77] + "..."
                residual_exaggeration_examples.append(f"{coord} ({m_exag.group(0)}): {snippet}")
        m_tmpl = RESIDUAL_TEMPLATE_PLACEHOLDER_RE.search(cleaned)
        if m_tmpl:
            residual_template_placeholders += 1
            if len(residual_template_placeholder_examples) < 20:
                snippet = cleaned.strip()
                if len(snippet) > 80:
                    snippet = snippet[:77] + "..."
                residual_template_placeholder_examples.append(f"{coord} ({m_tmpl.group(0)}): {snippet}")

    for p_idx, p in enumerate(document.paragraphs):
        if p.text:
            check_text(f"P{p_idx}", p.text)

    seen_tc: set[int] = set()

    def walk_tables(tables, prefix: str = "T") -> None:
        for t_idx, t in enumerate(tables):
            t_coord = f"{prefix}{t_idx}"
            for r_idx, row in enumerate(t.rows):
                for c_idx, cell in enumerate(row.cells):
                    tc_id = id(cell._tc)
                    if tc_id in seen_tc:
                        continue
                    seen_tc.add(tc_id)
                    c_coord = f"{t_coord}R{r_idx}C{c_idx}"
                    for p in cell.paragraphs:
                        if p.text:
                            check_text(c_coord, p.text)
                    if cell.tables:
                        walk_tables(cell.tables, prefix=f"{c_coord}_T")

    walk_tables(document.tables)
    return (
        residual_omml,
        residual_latex,
        residual_latex_examples,
        residual_work_codes,
        residual_work_code_examples,
        residual_exaggerations,
        residual_exaggeration_examples,
        residual_template_placeholders,
        residual_template_placeholder_examples,
    )




RAW_RUN_ASCII_MATH_RE = re.compile(r"[_^{}\\]")
MERGED_EQ_PAREN_RE = re.compile(r"\([^()]*=[^()]*\)|\[[^\[\]]*=[^\[\]]*\]")


def _omath_top_text(node: etree._Element) -> str:
    """Reconstruct top-level equation string with m:d delimiters restored and m:sub/m:sup excluded."""
    tag = etree.QName(node).localname
    if tag in ("sub", "sup", "deg"):
        return ""
    if tag == "t":
        return node.text or ""
    if tag == "d":
        beg = node.xpath("./m:dPr/m:begChr/@m:val", namespaces=NAMESPACES)
        end = node.xpath("./m:dPr/m:endChr/@m:val", namespaces=NAMESPACES)
        b_c = beg[0] if beg else "("
        e_c = end[0] if end else ")"
        inner = "".join(_omath_top_text(ch) for ch in node.xpath("./m:e", namespaces=NAMESPACES))
        return f"{b_c}{inner}{e_c}"
    return "".join(_omath_top_text(ch) for ch in node)


def _scan_raw_ascii_runs_and_merged_equations(document: Document, root: etree._Element) -> tuple[list[str], list[str]]:
    r"""
    1) Check every <w:r> text run in paragraphs and unique table cells (outside <m:oMath>)
       for raw _, ^, {, }, or \ characters.
    2) Check every <m:oMathPara> display equation for merged secondary equations on the same line.
    """
    raw_run_hits: list[str] = []
    for p_idx, p in enumerate(document.paragraphs):
        run_txt = "".join(r.text for r in p.runs if r.text)
        cleaned = OMML_PLACEHOLDER_STRIP_RE.sub("", run_txt)
        m = RAW_RUN_ASCII_MATH_RE.search(cleaned)
        if m and len(raw_run_hits) < 25:
            raw_run_hits.append(f"P{p_idx} ({m.group(0)}): {cleaned.strip()[:80]}")

    seen_tc: set[int] = set()
    for t_idx, t in enumerate(document.tables):
        for r_idx, row in enumerate(t.rows):
            for c_idx, cell in enumerate(row.cells):
                tc_id = id(cell._tc)
                if tc_id in seen_tc:
                    continue
                seen_tc.add(tc_id)
                run_txt = "".join(r.text for p in cell.paragraphs for r in p.runs if r.text)
                cleaned = OMML_PLACEHOLDER_STRIP_RE.sub("", run_txt)
                m = RAW_RUN_ASCII_MATH_RE.search(cleaned)
                if m and len(raw_run_hits) < 25:
                    raw_run_hits.append(f"T{t_idx}R{r_idx}C{c_idx} ({m.group(0)}): {cleaned.strip()[:80]}")

    merged_eq_hits: list[str] = []
    for eq_idx, omath_para in enumerate(root.xpath(".//m:oMathPara", namespaces=NAMESPACES)):
        omaths = omath_para.xpath("./m:oMath", namespaces=NAMESPACES)
        eq_txt = _omath_top_text(omath_para).strip()
        if len(omaths) > 1:
            merged_eq_hits.append(f"Eq#{eq_idx} (multiple m:oMath in one m:oMathPara): {eq_txt[:80]}")
            continue
        eq_body = re.sub(r"\(\s*S?\d+[a-z]?\s*\)\s*$", "", eq_txt).strip()
        # Strip balanced (...) before checking comma/semicolon-separated multiple equations
        no_parens = eq_body
        while re.search(r"\([^()]+\)", no_parens):
            no_parens = re.sub(r"\([^()]+\)", "", no_parens)
        multi_comma_eq = sum(1 for seg in re.split(r"[,;\u2003]+", no_parens) if "=" in seg) >= 2
        if MERGED_EQ_PAREN_RE.search(eq_body) or multi_comma_eq:
            merged_eq_hits.append(f"Eq#{eq_idx} (merged side-equation on display line): {eq_txt[:80]}")

    return raw_run_hits, merged_eq_hits


def _audit_disk_provenance(document: Document, provenance_dir: Path) -> tuple[bool, list[str]]:
    """
    Cross-project Ground-Truth Disk Provenance Gate:
    Parses actual simulation input/output files in provenance_dir (.mdp, .gro, provenance_assertions.json)
    and verifies that the DOCX text matches disk ground truth with zero fabricated template tokens.
    """
    provenance_dir = provenance_dir.expanduser().resolve()
    errors: list[str] = []
    if not provenance_dir.is_dir():
        return False, [f"provenance_dir does not exist: {provenance_dir}"]

    full_text = "\n".join(
        ["".join(p._element.itertext()) for p in document.paragraphs]
        + ["".join(c._tc.itertext()) for t in document.tables for r in t.rows for c in r.cells]
    )

    # 1. Check optional explicit provenance_assertions.json if present
    assertions_file = provenance_dir / "provenance_assertions.json"
    if assertions_file.is_file():
        spec = json.loads(assertions_file.read_text(encoding="utf-8"))
        for req in spec.get("required_substrings", []):
            if str(req) not in full_text:
                errors.append(f"missing required ground-truth substring from provenance_assertions.json: {req!r}")
        for fb in spec.get("forbidden_substrings", []):
            if str(fb) in full_text:
                errors.append(f"found forbidden template/hallucinated substring: {fb!r}")

    # 2. Auto-detect GROMACS c01..c10.mdp pressure schedule if present under runs/r01/*
    r01_dirs = sorted((provenance_dir / "runs" / "r01").glob("*")) if (provenance_dir / "runs" / "r01").is_dir() else []
    for u_dir in r01_dirs[:1]:
        ref_ps = []
        for i in range(1, 11):
            mdp_p = u_dir / f"c{i:02d}.mdp"
            if not mdp_p.exists():
                mdp_p = u_dir / f"c{i:02d}_sub1.mdp"
            if mdp_p.is_file():
                for ln in mdp_p.read_text(encoding="utf-8", errors="ignore").splitlines():
                    if ln.strip().startswith("ref-p"):
                        ref_ps.append(f"{float(ln.split('=')[1].strip()):.1f}")
                        break
        if len(ref_ps) == 10:
            exp_p = "[" + ", ".join(ref_ps) + "]"
            if exp_p not in full_text:
                errors.append(f"DOCX missing actual c01..c10.mdp ref-p schedule {exp_p} from {u_dir}")

    # 3. Auto-detect .gro atom counts across runs/r01/*/c10.gro
    for u_dir in r01_dirs:
        gro_p = u_dir / "c10.gro"
        if gro_p.is_file():
            lines = gro_p.read_text(encoding="utf-8", errors="ignore").splitlines()
            if len(lines) >= 2 and lines[1].strip().isdigit():
                n_at = int(lines[1].strip())
                if f"{n_at:,}" not in full_text and str(n_at) not in full_text:
                    errors.append(f"DOCX missing actual atom count {n_at:,} from {gro_p}")

    return len(errors) == 0, errors


SYNTHETIC_RANDOM_CALL_RE = re.compile(
    r"\b(?:np\.random\.(?:normal|randn|uniform|rand|random)|random\.(?:gauss|normalvariate|uniform|random)|rng\.(?:normal|uniform))\s*\("
)


def _audit_figure_scripts_no_synthetic(script_paths: list[Path]) -> tuple[bool, list[str]]:
    """
    Scan figure-generation Python scripts to block unauthorized synthetic random scatter/curves
    (e.g., np.random.normal in force-field or RESP parity plots) unless explicitly marked with
    # AWF_ALLOW_MONTE_CARLO on that line.
    """
    hits: list[str] = []
    for sp in script_paths:
        sp = sp.expanduser().resolve()
        if not sp.is_file():
            hits.append(f"figure script does not exist: {sp}")
            continue
        for lineno, line in enumerate(sp.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#") or "AWF_ALLOW_MONTE_CARLO" in line:
                continue
            m = SYNTHETIC_RANDOM_CALL_RE.search(line)
            if m:
                hits.append(f"{sp.name}:{lineno} ({m.group(0)}): {stripped[:80]}")
    return len(hits) == 0, hits


CJK_IN_TABLE_RE = re.compile(r"[\u4e00-\u9fff]")


def _count_cjk_table_cells(doc: Document) -> list[dict]:
    hits: list[dict] = []
    for t_idx, table in enumerate(doc.tables):
        for r_idx, row in enumerate(table.rows):
            for c_idx, cell in enumerate(row.cells):
                txt = (cell.text or "").strip()
                if CJK_IN_TABLE_RE.search(txt):
                    hits.append({
                        "table_index": t_idx,
                        "row_index": r_idx,
                        "col_index": c_idx,
                        "snippet": txt[:80],
                    })
    return hits


def _scan_table_column_consistency(doc: Document) -> list[str]:
    """Verify every table has a consistent number of grid columns across all rows (no truncated width arrays)."""
    issues: list[str] = []
    for t_idx, table in enumerate(doc.tables):
        if not table.rows:
            continue
        expected_cols = len(table.rows[0].cells)
        for r_idx, row in enumerate(table.rows):
            if len(row.cells) != expected_cols:
                issues.append(f"T{t_idx}R{r_idx}: expected {expected_cols} cols, got {len(row.cells)}")
    return issues


def inspect_docx(path: Path) -> dict:
    path = path.expanduser().resolve()
    result = {
        "path": str(path),
        "exists": path.is_file(),
        "zip_integrity": False,
        "python_docx_parse": False,
        "errors": [],
    }
    if not path.is_file():
        result["errors"].append("file does not exist")
        return result
    try:
        with zipfile.ZipFile(path) as archive:
            bad_member = archive.testzip()
            if bad_member:
                result["errors"].append(f"CRC failure in {bad_member}")
                return result
            result["zip_integrity"] = True
            names = set(archive.namelist())
            required = {"[Content_Types].xml", "word/document.xml"}
            missing = sorted(required - names)
            if missing:
                result["errors"].append(f"missing required members: {missing}")
                return result
            document_xml = archive.read("word/document.xml")
            root = etree.fromstring(document_xml)
            total_math = int(root.xpath("count(.//m:oMath)", namespaces=NAMESPACES))
            display_math = int(root.xpath("count(.//m:oMathPara)", namespaces=NAMESPACES))
            result["equations"] = total_math
            result["display_equations"] = display_math
            result["inline_equations"] = int(
                root.xpath("count(.//m:oMath[not(ancestor::m:oMathPara)])", namespaces=NAMESPACES)
            )
            result["drawings"] = int(root.xpath("count(.//w:drawing)", namespaces=NAMESPACES))
            result["clipped_equation_paragraphs"] = int(
                root.xpath(
                    "count(.//w:p[.//m:oMathPara and ./w:pPr/w:spacing[@w:lineRule='exact']])",
                    namespaces=NAMESPACES,
                )
            )
            result["clipped_drawing_paragraphs"] = int(
                root.xpath(
                    "count(.//w:p[.//w:drawing and ./w:pPr/w:spacing[@w:lineRule='exact']])",
                    namespaces=NAMESPACES,
                )
            )
            media_names = sorted(name for name in names if name.startswith("word/media/") and not name.endswith("/"))
            media_hashes = [_hash(archive.read(name)) for name in media_names]
            result["media_count"] = len(media_names)
            result["media_names"] = media_names
            result["media_hashes"] = media_hashes
    except (zipfile.BadZipFile, KeyError, etree.XMLSyntaxError, OSError) as exc:
        result["errors"].append(f"package parse failed: {exc}")
        return result
    try:
        document = Document(path)
        result["python_docx_parse"] = True
        result["body_paragraphs"] = len(document.paragraphs)
        result["tables"] = len(document.tables)
        result["sections"] = len(document.sections)
        (
            residual_omml,
            residual_latex,
            residual_latex_examples,
            residual_work_codes,
            residual_work_code_examples,
            residual_exaggerations,
            residual_exaggeration_examples,
            residual_template_placeholders,
            residual_template_placeholder_examples,
        ) = _scan_text_blocks(document)
        result["residual_omml_placeholders"] = residual_omml
        result["residual_latex_tokens"] = residual_latex
        result["residual_latex_examples"] = residual_latex_examples
        result["residual_work_codes"] = residual_work_codes
        result["residual_work_code_examples"] = residual_work_code_examples
        result["residual_exaggerations"] = residual_exaggerations
        result["residual_exaggeration_examples"] = residual_exaggeration_examples
        result["residual_template_placeholders"] = residual_template_placeholders
        result["residual_template_placeholder_examples"] = residual_template_placeholder_examples
        cjk_hits = _count_cjk_table_cells(document)
        result["table_cjk_cell_count"] = len(cjk_hits)
        result["table_cjk_cell_examples"] = cjk_hits[:10]
        raw_run_hits, merged_eq_hits = _scan_raw_ascii_runs_and_merged_equations(document, root)
        result["raw_ascii_math_run_count"] = len(raw_run_hits)
        result["raw_ascii_math_run_examples"] = raw_run_hits
        result["merged_display_equation_count"] = len(merged_eq_hits)
        result["merged_display_equation_examples"] = merged_eq_hits
        trunc_cols = _scan_table_column_consistency(document)
        result["truncated_table_row_count"] = len(trunc_cols)
        result["truncated_table_row_examples"] = trunc_cols[:10]
    except Exception as exc:  # python-docx exposes several parser exceptions
        result["errors"].append(f"python-docx parse failed: {exc}")
    return result


def audit(
    path: Path,
    baseline: Path | None = None,
    expected_equations: int | None = None,
    minimum_equations: int | None = None,
    max_media: int | None = None,
    max_new_media: int | None = None,
    require_english_tables: bool = False,
    provenance_dir: Path | None = None,
    figure_scripts: list[Path] | None = None,
) -> dict:
    current = inspect_docx(path)
    checks = {
        "zip_integrity": bool(current.get("zip_integrity")),
        "python_docx_parse": bool(current.get("python_docx_parse")),
        "no_package_errors": not current.get("errors"),
        "no_unrendered_omml_placeholders": current.get("residual_omml_placeholders", 0) == 0,
        "no_residual_latex_tokens": current.get("residual_latex_tokens", 0) == 0,
        "no_residual_work_codes": current.get("residual_work_codes", 0) == 0,
        "no_exaggerated_claims": current.get("residual_exaggerations", 0) == 0,
        "no_residual_template_placeholders": current.get("residual_template_placeholders", 0) == 0,
        "no_clipped_display_equations": current.get("clipped_equation_paragraphs", 0) == 0,
        "no_clipped_drawings": current.get("clipped_drawing_paragraphs", 0) == 0,
        "no_chinese_in_english_tables": (current.get("table_cjk_cell_count", 0) == 0) if require_english_tables else True,
        "no_raw_sub_superscript_ascii_in_runs": current.get("raw_ascii_math_run_count", 0) == 0,
        "no_merged_display_equations": current.get("merged_display_equation_count", 0) == 0,
        "no_truncated_table_columns": current.get("truncated_table_row_count", 0) == 0,
    }
    if figure_scripts:
        fig_ok, fig_errs = _audit_figure_scripts_no_synthetic(figure_scripts)
        checks["no_synthetic_random_in_figure_scripts"] = fig_ok
        current["figure_script_synthetic_errors"] = fig_errs
    if provenance_dir is not None and current.get("python_docx_parse"):
        prov_ok, prov_errs = _audit_disk_provenance(Document(path), provenance_dir)
        checks["disk_provenance_concordance"] = prov_ok
        current["provenance_errors"] = prov_errs
    if expected_equations is not None:
        checks["expected_equations"] = current.get("equations") == expected_equations
    if minimum_equations is not None:
        checks["minimum_equations"] = current.get("equations", 0) >= minimum_equations
    if max_media is not None:
        checks["max_media"] = current.get("media_count", 0) <= max_media

    baseline_info = None
    new_media = None
    if baseline is not None:
        baseline_info = inspect_docx(baseline)
        current_counter = Counter(current.get("media_hashes", []))
        baseline_counter = Counter(baseline_info.get("media_hashes", []))
        new_media = sum((current_counter - baseline_counter).values())
        checks["baseline_zip_integrity"] = bool(baseline_info.get("zip_integrity"))
        checks["baseline_python_docx_parse"] = bool(baseline_info.get("python_docx_parse"))
        if max_new_media is not None:
            checks["max_new_media"] = new_media <= max_new_media
    elif max_new_media is not None:
        checks["max_new_media_requires_baseline"] = False

    return {
        "pass": all(checks.values()),
        "checks": checks,
        "document": current,
        "baseline": baseline_info,
        "new_media_objects": new_media,
        "desktop_word_open_test": "not_run",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("docx", type=Path)
    parser.add_argument("--baseline", type=Path)
    equation_group = parser.add_mutually_exclusive_group()
    equation_group.add_argument("--expected-equations", type=int)
    equation_group.add_argument("--minimum-equations", type=int)
    parser.add_argument("--max-media", type=int)
    parser.add_argument("--max-new-media", type=int)
    parser.add_argument("--require-english-tables", action="store_true")
    parser.add_argument("--provenance-dir", type=Path, help="Project/campaign directory to verify .mdp/.gro/JSON ground-truth provenance against DOCX")
    parser.add_argument("--figure-scripts", type=Path, nargs="*", help="Figure-generating Python scripts to scan for unauthorized synthetic random calls")
    parser.add_argument("--json-out", type=Path)
    return parser


def main() -> int:
    arguments = build_parser().parse_args()
    report = audit(
        arguments.docx,
        baseline=arguments.baseline,
        expected_equations=arguments.expected_equations,
        minimum_equations=arguments.minimum_equations,
        max_media=arguments.max_media,
        max_new_media=arguments.max_new_media,
        require_english_tables=arguments.require_english_tables,
        provenance_dir=arguments.provenance_dir,
        figure_scripts=arguments.figure_scripts,
    )
    payload = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    print(payload)
    if arguments.json_out:
        arguments.json_out.write_text(payload + "\n", encoding="utf-8")
    return 0 if report["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
