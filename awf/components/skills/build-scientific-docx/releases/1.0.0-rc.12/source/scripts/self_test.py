#!/usr/bin/env python3
"""Positive and negative regression tests for the scientific DOCX helpers."""

from __future__ import annotations

from pathlib import Path
import re
import tempfile
import zipfile

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from lxml import etree

import audit_docx
import native_math
import test_figure_sync_rule


NAMESPACES = {
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def get_document_xml(docx_path: Path) -> etree._Element:
    with zipfile.ZipFile(docx_path) as archive:
        return etree.fromstring(archive.read("word/document.xml"))


def test_user_preservation_and_file_safety(root: Path) -> None:
    source = root / "user-edited-source.docx"
    output = root / "native-equations.docx"

    document = Document()
    document.add_paragraph("USER EDIT MUST SURVIVE")
    table = document.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "symbol"
    table.cell(0, 1).text = "meaning"
    document.add_paragraph(r"{{OMML: S_{cov}=\frac{N_{IC-IC}}{N_{all}}-\bar{x}}}")
    source.parent.mkdir(parents=True, exist_ok=True)
    document.save(source)

    count = native_math.render_file(source, output)
    require(count == 1, "expected exactly one converted placeholder")
    report = audit_docx.audit(
        output,
        baseline=source,
        expected_equations=1,
        max_new_media=0,
    )
    require(report["pass"], f"positive audit failed: {report}")
    rebuilt = Document(output)
    require(any(p.text == "USER EDIT MUST SURVIVE" for p in rebuilt.paragraphs), "user paragraph lost")
    require(len(rebuilt.tables) == 1, "user table lost")

    try:
        native_math.render_file(source, source)
    except ValueError:
        pass
    else:
        raise AssertionError("same-path input/output was not rejected")

    try:
        native_math.render_file(source, output)
    except FileExistsError:
        pass
    else:
        raise AssertionError("existing output was overwritten")

    negative = audit_docx.audit(source, expected_equations=1)
    require(not negative["pass"], "missing native equation was not detected")
    require(
        not negative["checks"]["no_unrendered_omml_placeholders"],
        "unrendered {{OMML placeholder was not flagged",
    )


def test_nary_semantics(root: Path) -> None:
    fixture_path = root / "nary_semantics.docx"
    formulas = [
        r"\sum_{i=1}^{n} x_i",
        r"\sum_{i=1} x_i",
        r"\prod^{N} x_i",
        r"\int x",
    ]
    native_math.create_file(fixture_path, formulas)
    report = audit_docx.audit(fixture_path, expected_equations=4, max_media=0)
    require(report["pass"], f"n-ary audit failed: {report}")

    tree = get_document_xml(fixture_path)

    for script_tag in ["m:sSubSup", "m:sSub", "m:sSup"]:
        for elem in tree.xpath(f".//{script_tag}", namespaces=NAMESPACES):
            for text in elem.xpath("./m:e//m:t/text()", namespaces=NAMESPACES):
                require(
                    text not in {"∑", "∏", "∫"},
                    f"n-ary operator glyph '{text}' fell back to {script_tag}",
                )

    maths = tree.xpath(".//m:oMath", namespaces=NAMESPACES)
    require(len(maths) == 4, f"expected 4 math blocks, got {len(maths)}")

    n0 = maths[0].xpath(".//m:nary", namespaces=NAMESPACES)[0]
    require(n0.xpath("./m:naryPr/m:chr/@m:val", namespaces=NAMESPACES) == ["∑"], "m0 chr")
    require(len(n0.xpath("./m:naryPr/m:subHide", namespaces=NAMESPACES)) == 0, "m0 subHide present")
    require(len(n0.xpath("./m:naryPr/m:supHide", namespaces=NAMESPACES)) == 0, "m0 supHide present")
    require("".join(n0.xpath("./m:sub//m:t/text()", namespaces=NAMESPACES)).strip() == "i=1", "m0 sub")
    require("".join(n0.xpath("./m:sup//m:t/text()", namespaces=NAMESPACES)).strip() == "n", "m0 sup")
    require("".join(n0.xpath("./m:e//m:t/text()", namespaces=NAMESPACES)).strip() == "xi", "m0 body")

    n1 = maths[1].xpath(".//m:nary", namespaces=NAMESPACES)[0]
    require(n1.xpath("./m:naryPr/m:chr/@m:val", namespaces=NAMESPACES) == ["∑"], "m1 chr")
    require(len(n1.xpath("./m:naryPr/m:subHide", namespaces=NAMESPACES)) == 0, "m1 subHide present")
    require(n1.xpath("./m:naryPr/m:supHide/@m:val", namespaces=NAMESPACES) == ["1"], "m1 supHide val")
    require("".join(n1.xpath("./m:sub//m:t/text()", namespaces=NAMESPACES)).strip() == "i=1", "m1 sub")
    require(len(n1.xpath("./m:sup//m:t", namespaces=NAMESPACES)) == 0, "m1 sup not empty")
    require("".join(n1.xpath("./m:e//m:t/text()", namespaces=NAMESPACES)).strip() == "xi", "m1 body")

    n2 = maths[2].xpath(".//m:nary", namespaces=NAMESPACES)[0]
    require(n2.xpath("./m:naryPr/m:chr/@m:val", namespaces=NAMESPACES) == ["∏"], "m2 chr")
    require(n2.xpath("./m:naryPr/m:subHide/@m:val", namespaces=NAMESPACES) == ["1"], "m2 subHide val")
    require(len(n2.xpath("./m:naryPr/m:supHide", namespaces=NAMESPACES)) == 0, "m2 supHide present")
    require(len(n2.xpath("./m:sub//m:t", namespaces=NAMESPACES)) == 0, "m2 sub not empty")
    require("".join(n2.xpath("./m:sup//m:t/text()", namespaces=NAMESPACES)).strip() == "N", "m2 sup")
    require("".join(n2.xpath("./m:e//m:t/text()", namespaces=NAMESPACES)).strip() == "xi", "m2 body")

    n3 = maths[3].xpath(".//m:nary", namespaces=NAMESPACES)[0]
    require(n3.xpath("./m:naryPr/m:chr/@m:val", namespaces=NAMESPACES) == ["∫"], "m3 chr")
    require(n3.xpath("./m:naryPr/m:subHide/@m:val", namespaces=NAMESPACES) == ["1"], "m3 subHide val")
    require(n3.xpath("./m:naryPr/m:supHide/@m:val", namespaces=NAMESPACES) == ["1"], "m3 supHide val")
    require(len(n3.xpath("./m:sub//m:t", namespaces=NAMESPACES)) == 0, "m3 sub not empty")
    require(len(n3.xpath("./m:sup//m:t", namespaces=NAMESPACES)) == 0, "m3 sup not empty")
    require("".join(n3.xpath("./m:e//m:t/text()", namespaces=NAMESPACES)).strip() == "x", "m3 body")


def test_paired_delimiters(root: Path) -> None:
    fixture_path = root / "paired_delimiters.docx"
    formulas = [
        r"\left( x \right)",
        r"\left[ x \right]",
        r"\left\{ x \right\}",
        r"\left\langle x \right\rangle",
        r"\left| x \right|",
        r"\left\Vert x \right\Vert",
        r"\left. \frac{df}{dx} \right|_{x=0}",
        r"\left| x \right.",
    ]
    native_math.create_file(fixture_path, formulas)
    report = audit_docx.audit(fixture_path, expected_equations=8, max_media=0)
    require(report["pass"], f"delimiters audit failed: {report}")

    tree = get_document_xml(fixture_path)
    maths = tree.xpath(".//m:oMath", namespaces=NAMESPACES)
    require(len(maths) == 8, f"expected 8 math blocks, got {len(maths)}")

    expected_specs = [
        ("(", ")"),
        ("[", "]"),
        ("{", "}"),
        ("⟨", "⟩"),
        ("|", "|"),
        ("‖", "‖"),
        ("", "|"),
        ("|", ""),
    ]

    for m, (exp_beg, exp_end) in zip(maths, expected_specs):
        d_elems = m.xpath(".//m:d", namespaces=NAMESPACES)
        require(len(d_elems) >= 1, "missing m:d delimiter element")
        d = d_elems[0]
        beg_val = d.xpath("./m:dPr/m:begChr/@m:val", namespaces=NAMESPACES)[0]
        end_val = d.xpath("./m:dPr/m:endChr/@m:val", namespaces=NAMESPACES)[0]
        require(beg_val == exp_beg, f"delimiter begChr expected '{exp_beg}', got '{beg_val}'")
        require(end_val == exp_end, f"delimiter endChr expected '{exp_end}', got '{end_val}'")
        require(len(d.xpath("./m:e", namespaces=NAMESPACES)) == 1, "m:d missing body m:e")

        plain_runs = m.xpath("./m:r//m:t/text()", namespaces=NAMESPACES)
        for t in plain_runs:
            require(
                t not in {"(", ")", "[", "]", "{", "}", "|", "‖", "⟨", "⟩"},
                f"delimiter emitted as plain run: '{t}'",
            )


def test_raw_absolute_value(root: Path) -> None:
    fixture_path = root / "raw_absolute_value.docx"
    formulas = [
        r"|x|",
        r"|y_i - y_{i,\mathrm{pred}}|",
        r"|C_{\mathrm{decay}}|",
        r"|{x + y}|",
        r"|(x + y)|",
        r"| [x] |",
        r"{|x|}",
        r"(|x|)",
        r"\left( |x| \right)",
        r"\left| |x| \right|",
        r"|(|x|)|",
        r"|{|x|}|",
        r"|x| + |y|",
        r"|x|^2",
    ]
    native_math.create_file(fixture_path, formulas)
    report = audit_docx.audit(fixture_path, expected_equations=len(formulas), max_media=0)
    require(report["pass"], f"raw absolute value audit failed: {report}")


def test_named_functions(root: Path) -> None:
    fixture_path = root / "named_functions.docx"
    formulas = [
        r"\ln\left(x\right)",
        r"\exp\left(y\right)",
        r"\max\left(a,b\right)",
        r"\ln x^2",
    ]
    native_math.create_file(fixture_path, formulas)
    report = audit_docx.audit(fixture_path, expected_equations=4, max_media=0)
    require(report["pass"], f"named functions audit failed: {report}")


def test_operatorname_semantics(root: Path) -> None:
    fixture_path = root / "operatorname_semantics.docx"
    formulas = [
        r"\operatorname{median}(x)",
        r"\mathrm{MdARE} = \operatorname{median}\left( \frac{|y_i - y_{i,\mathrm{pred}}|}{y_i} \right) \times 100\%",
        r"\operatorname{customFunc}{x}",
        r"\operatorname{median} x^2",
        r"\mathrm{median}",
        r"\text{median}",
    ]
    native_math.create_file(fixture_path, formulas)
    report = audit_docx.audit(fixture_path, expected_equations=6, max_media=0)
    require(report["pass"], f"operatorname audit failed: {report}")


def test_hat_accent_and_bar_preservation(root: Path) -> None:
    fixture_path = root / "accents_and_bars.docx"
    formulas = [
        r"\hat{x}",
        r"\hat{y}_i",
        r"\bar{x}",
        r"\overline{y}",
        r"\tilde{F}",
        r"\vec{v}_i",
        r"\dot{T}_e",
        r"\ddot{R}_I",
        r"T_e \gg T_l",
        r"\Delta E(T_e) \ll \Delta E_0",
        r"\hbar \omega \to E_d^\circ",
        r"\mathrm{C=O} + e^- \rightleftharpoons \mathrm{C-O}^{\bullet -}",
    ]
    native_math.create_file(fixture_path, formulas)
    report = audit_docx.audit(fixture_path, expected_equations=len(formulas), max_media=0)
    require(report["pass"], f"accents and expanded symbols audit failed: {report}")

    tree = get_document_xml(fixture_path)
    maths = tree.xpath(".//m:oMath", namespaces=NAMESPACES)
    require(len(maths) == len(formulas), f"expected {len(formulas)} math blocks")

    expected_acc_chrs = ["^", "^", None, None, "~", "→", "˙", "¨"]
    for idx, exp_chr in enumerate(expected_acc_chrs):
        if exp_chr is not None:
            acc = maths[idx].xpath(".//m:acc", namespaces=NAMESPACES)[0]
            require(
                acc.xpath("./m:accPr/m:chr/@m:val", namespaces=NAMESPACES) == [exp_chr],
                f"formula {idx} expected acc chr {exp_chr}",
            )


def test_inline_omml_and_unclipped_layout(root: Path) -> None:
    src = root / "inline_and_clipped_src.docx"
    dst = root / "inline_and_clipped_dst.docx"

    doc = Document()
    # 1. Paragraph with exact 28pt line spacing and first-line indent containing display OMML
    p_disp = doc.add_paragraph("{{OMML: C_e(T_e) \\frac{\\partial T_e}{\\partial t} = G(T_e)(T_l - T_e)}}")
    pPr = p_disp._p.get_or_add_pPr()
    ind = OxmlElement("w:ind")
    ind.set(qn("w:firstLine"), "560")
    pPr.append(ind)
    sp = OxmlElement("w:spacing")
    sp.set(qn("w:line"), "560")
    sp.set(qn("w:lineRule"), "exact")
    pPr.append(sp)

    # 2. Paragraph with inline OMML placeholders
    doc.add_paragraph("电子热容 {{OMML_INLINE: C_e(T_e)}} 与电声耦合系数 {{OMML_INLINE: G(T_e)}} 随温度变化。")
    doc.save(src)

    count = native_math.render_file(src, dst)
    require(count == 3, f"expected 3 rendered equations (1 display + 2 inline), got {count}")

    report = audit_docx.audit(dst, baseline=src, expected_equations=3, max_new_media=0)
    require(report["pass"], f"inline + unclipped audit failed: {report}")
    require(report["document"]["display_equations"] == 1, "expected 1 display equation")
    require(report["document"]["inline_equations"] == 2, "expected 2 inline equations")
    require(report["document"]["clipped_equation_paragraphs"] == 0, "expected 0 clipped display equations")

    # Negative check: manually re-inject exact line spacing on a display equation paragraph and verify audit fails
    bad_dst = root / "clipped_bad.docx"
    bad_doc = Document(dst)
    for p in bad_doc.paragraphs:
        if len(p._p.findall(".//" + qn("m:oMathPara"))) > 0:
            pPr_bad = p._p.get_or_add_pPr()
            sp_bad = OxmlElement("w:spacing")
            sp_bad.set(qn("w:line"), "560")
            sp_bad.set(qn("w:lineRule"), "exact")
            pPr_bad.append(sp_bad)
    bad_doc.save(bad_dst)
    bad_report = audit_docx.audit(bad_dst, expected_equations=3)
    require(not bad_report["pass"], "clipped display equation should fail audit")
    require(
        not bad_report["checks"]["no_clipped_display_equations"],
        "no_clipped_display_equations check should be False",
    )


def test_table_pipe_safety_and_residual_token_audit(root: Path) -> None:
    md_row = "| 1D 链极化子带宽 ($W_v = 2|J_h|$) | $0.436\\text{ eV}$ |"

    # 1. Demonstrate that bare .split("|") corrupts |J_h| into broken $ tokens and fails audit
    bad_cells = [c.strip() for c in md_row.strip().strip("|").split("|")]
    bad_docx = root / "table_pipe_corrupted.docx"
    bad_doc = Document()
    t_bad = bad_doc.add_table(rows=1, cols=len(bad_cells))
    for idx, val in enumerate(bad_cells):
        t_bad.cell(0, idx).text = val
    bad_doc.add_paragraph("参见 PPT 第 15 页 与 Slide 9 的内部记录。")
    bad_doc.add_paragraph("该结果从根本上解释了三支柱动力学微观机理，其中第一动力学支柱彻底消除了界面势垒。")
    bad_doc.save(bad_docx)

    bad_report = audit_docx.audit(bad_docx)
    require(not bad_report["pass"], "corrupted table pipe, work code, and exaggerated claims should fail audit")
    require(
        not bad_report["checks"]["no_residual_latex_tokens"],
        "broken $ / LaTeX tokens in table cells must fail no_residual_latex_tokens",
    )
    require(
        not bad_report["checks"]["no_residual_work_codes"],
        "PPT 第 X 页 / Slide N must fail no_residual_work_codes",
    )
    require(
        not bad_report["checks"]["no_exaggerated_claims"],
        "exaggerated phrasing (从根本上 / 三支柱 / 第一动力学支柱 / 彻底消除) must fail no_exaggerated_claims",
    )

    # 2. Demonstrate that whitespace-bounded pipe splitting re.split(r"\s+\|\s+", ...) + inline OMML + measured prose passes cleanly
    good_cells = [c.strip() for c in re.split(r"\s+\|\s+", md_row.strip().strip("|"))]
    require(len(good_cells) == 2, f"expected 2 columns with whitespace-bounded pipe split, got {len(good_cells)}")
    good_src = root / "table_pipe_clean_src.docx"
    good_dst = root / "table_pipe_clean_dst.docx"
    good_doc = Document()
    t_good = good_doc.add_table(rows=1, cols=len(good_cells))
    for idx, val in enumerate(good_cells):
        converted = re.sub(r"\$([^$]+)\$", lambda m: f"{{{{OMML_INLINE: {m.group(1)}}}}}", val)
        t_good.cell(0, idx).text = converted
    good_doc.add_paragraph("该结果解释了动力学微观机理，其中第一个动力学有利因素缓解了界面势垒。")
    good_doc.save(good_src)

    eq_count = native_math.render_file(good_src, good_dst)
    require(eq_count == 2, f"expected 2 inline table equations, got {eq_count}")
    good_report = audit_docx.audit(good_dst, expected_equations=2, max_media=0)
    require(good_report["pass"], f"clean table pipe + OMML + measured prose should pass audit: {good_report}")
    require(good_report["checks"]["no_exaggerated_claims"], "measured prose must pass no_exaggerated_claims")


def test_representative_corpus(root: Path) -> None:
    fixture_path = root / "representative_corpus.docx"
    corpus = [
        r"\sum_{i=1}^{n}(y_i-\bar{y})^2",
        r"\ln\left(I_c(E,t)\right)=a_c+b_c\ln\left(E\right)-\frac{t}{\tau_c(E)}",
        r"\tau_c(E)=\exp\left(g_c\right)\cdot E^{d_c}",
        r"R^2=1-\frac{\sum_i\left(y_i-\hat{y}_i\right)^2}{\sum_i\left(y_i-\bar{y}\right)^2}",
        r"\max\left(E,0\right)",
        r"\left|y_i-\hat{y}_i\right|",
    ]
    native_math.create_file(fixture_path, corpus)
    report = audit_docx.audit(fixture_path, expected_equations=6, max_media=0)
    require(report["pass"], f"representative corpus audit failed: {report}")


def test_negative_syntax_rejections() -> None:
    negative_suites: dict[str, list[str]] = {
        "missing nary body": [
            r"\sum",
            r"\sum_{i=1}^n",
            r"\sum_{i=1}^n {}",
            r"\prod",
            r"\int_0^\infty",
        ],
        "missing function argument": [
            r"\ln",
            r"\ln{}",
            r"\exp",
            r"\max",
            r"\ln \right)",
        ],
        "unmatched left/right": [
            r"\left( x",
            r"x \right)",
            r"\left( x \right",
            r"\left",
            r"\right",
        ],
        "duplicate scripts": [
            r"x_1_2",
            r"x^1^2",
            r"x_a_b",
            r"x^a^b",
            r"\sum_{i=1}_j x",
            r"\sum^a^b x",
        ],
        "unsupported commands": [
            r"\definitelyUnsupported{y}",
            r"\foo{x}",
            r"\matrix{a}",
            r"\sqrt[3]{x}",
        ],
        "unmatched raw absolute value": [
            r"|x",
            r"x|",
            r"|x| | y",
            r"x | |y|",
            r"|",
            r"|||",
            r"(|)",
            r"|)|",
            r"{|}",
            r"|}|",
            r"[|]",
            r"|]|",
            r"\left( | \right)",
            r"| \right)",
            r"||",
            r"| |",
            r"||x||",
        ],
        "missing operatorname name or argument": [
            r"\operatorname",
            r"\operatorname{}",
            r"\operatorname{  }",
            r"\operatorname{median}",
            r"\operatorname{median}{}",
            r"\operatorname{median} \right)",
            r"\operatorname{median} )",
            r"\operatorname{median} }",
        ],
    }

    for category, expressions in negative_suites.items():
        for expr in expressions:
            try:
                native_math.LatexParser(expr).parse()
            except native_math.LatexSyntaxError:
                pass
            else:
                raise AssertionError(
                    f"negative test failed: '{expr}' in category '{category}' was not rejected"
                )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="scientific-docx-self-test-") as directory:
        root = Path(directory)
        test_user_preservation_and_file_safety(root)
        test_nary_semantics(root)
        test_paired_delimiters(root)
        test_raw_absolute_value(root)
        test_named_functions(root)
        test_operatorname_semantics(root)
        test_hat_accent_and_bar_preservation(root)
        test_inline_omml_and_unclipped_layout(root)
        test_table_pipe_safety_and_residual_token_audit(root)
        test_representative_corpus(root)
        test_negative_syntax_rejections()

        # Test rc.7 clean_omml_braces, \iint, \min_{A}, and require_english_tables
        doc_rc7 = Document()
        doc_rc7.add_paragraph("Surface integral {{OMML_INLINE: \\iint_{S} \\mathrm{min}_{A}(x) \\mathrm{d}S}}} test.")
        tbl_en = doc_rc7.add_table(rows=2, cols=2)
        tbl_en.cell(0, 0).text = "Metric"
        tbl_en.cell(0, 1).text = "Value"
        tbl_en.cell(1, 0).text = "MPI (kcal {{OMML_INLINE: \\mathrm{mol^{-1}}}})"
        tbl_en.cell(1, 1).text = "11.08"
        rc7_in = root / "rc7_in.docx"
        rc7_out = root / "rc7_out.docx"
        doc_rc7.save(rc7_in)
        native_math.render_file(rc7_in, rc7_out)
        rep_rc7_en = audit_docx.audit(rc7_out, require_english_tables=True)
        require(rep_rc7_en["pass"], f"rc7 English table audit failed: {rep_rc7_en}")
        require(rep_rc7_en["checks"]["no_chinese_in_english_tables"] is True, "expected English table check true")

        doc_rc7_cn = Document(rc7_out)
        doc_rc7_cn.tables[0].cell(1, 0).text = "中文指标"
        rc7_cn_out = root / "rc7_cn_out.docx"
        doc_rc7_cn.save(rc7_cn_out)
        rep_rc7_cn = audit_docx.audit(rc7_cn_out, require_english_tables=True)
        require(rep_rc7_cn["checks"]["no_chinese_in_english_tables"] is False, "expected Chinese table cell to fail")
        require(rep_rc7_cn["document"]["table_cjk_cell_count"] == 1, "expected 1 CJK cell")

        require(test_figure_sync_rule.main() == 0, "figure sync rule check failed")

        # Test rc.9 gates: no_raw_sub_superscript_ascii_in_runs, no_merged_display_equations, disk_provenance_concordance
        bad_raw_doc = Document()
        bad_raw_doc.add_paragraph("Unrendered subscript E_CT and superscript 10^-4 in plain run.")
        bad_raw_path = root / "rc9_bad_raw.docx"
        bad_raw_doc.save(bad_raw_path)
        rep_bad_raw = audit_docx.audit(bad_raw_path)
        require(rep_bad_raw["checks"]["no_raw_sub_superscript_ascii_in_runs"] is False, "expected raw E_CT / 10^-4 to fail no_raw_sub_superscript_ascii_in_runs")

        bad_merge_in = root / "rc9_bad_merge_in.docx"
        bad_merge_out = root / "rc9_bad_merge_out.docx"
        doc_merge = Document()
        doc_merge.add_paragraph(r"{{OMML: k_{b} = \sum_{m=1}^{3} \lambda_m \qquad (r_0 = r_{\mathrm{DFT}})}}")
        doc_merge.save(bad_merge_in)
        native_math.render_file(bad_merge_in, bad_merge_out)
        rep_bad_merge = audit_docx.audit(bad_merge_out)
        require(rep_bad_merge["checks"]["no_merged_display_equations"] is False, "expected merged display equation with (r_0 = r_DFT) to fail no_merged_display_equations")

        prov_dir = root / "sim_campaign"
        (prov_dir / "runs" / "r01" / "sysA").mkdir(parents=True, exist_ok=True)
        for idx_c, pval in enumerate([2.0, 3.0, 20.0, 25.0, 30.0, 20.0, 10.0, 5.0, 1.0, 1.0], 1):
            (prov_dir / "runs" / "r01" / "sysA" / f"c{idx_c:02d}.mdp").write_text(f"ref-p = {pval}\n", encoding="utf-8")
        (prov_dir / "runs" / "r01" / "sysA" / "c10.gro").write_text("sysA\n105692\n", encoding="utf-8")
        prov_doc_good = Document()
        prov_doc_good.add_paragraph("Pressure schedule [2.0, 3.0, 20.0, 25.0, 30.0, 20.0, 10.0, 5.0, 1.0, 1.0] bar with 105,692 atoms.")
        prov_good_path = root / "rc9_prov_good.docx"
        prov_doc_good.save(prov_good_path)
        rep_prov_good = audit_docx.audit(prov_good_path, provenance_dir=prov_dir)
        require(rep_prov_good["pass"] and rep_prov_good["checks"]["disk_provenance_concordance"] is True, f"expected valid provenance to pass: {rep_prov_good}")

        prov_doc_bad = Document()
        prov_doc_bad.add_paragraph("Fabricated schedule [2, 3, 5, 10, 10, 10, 10, 10, 1, 1] bar with 98,488 atoms.")
        prov_bad_path = root / "rc9_prov_bad.docx"
        prov_doc_bad.save(prov_bad_path)
        rep_prov_bad = audit_docx.audit(prov_bad_path, provenance_dir=prov_dir)
        require(rep_prov_bad["checks"]["disk_provenance_concordance"] is False, "expected fabricated pressure/atom count to fail disk_provenance_concordance")



        # Test rc.10 gates: \ddagger / \dagger support, internal debugging jargon filter, and --figure-scripts synthetic random gate
        rc10_in = root / "rc10_ddagger_in.docx"
        rc10_out = root / "rc10_ddagger_out.docx"
        doc_rc10 = Document()
        doc_rc10.add_paragraph(
            r"{{OMML: \Delta E_{\mathrm{safe}}^{T_1} = \Delta G_{\mathrm{BET},0}^{\ddagger} + k_{\mathrm{B}}T\ln\left(\frac{V_0^{\mathrm{Dexter}}}{\langle V_{\mathrm{Dexter}}\rangle}\right)}}"
        )
        doc_rc10.save(rc10_in)
        native_math.render_file(rc10_in, rc10_out)
        good_fig_py = root / "good_fig.py"
        good_fig_py.write_text("import numpy as np\nx = np.linspace(0, 1, 10)\n", encoding="utf-8")
        rep_rc10_good = audit_docx.audit(rc10_out, expected_equations=1, figure_scripts=[good_fig_py])
        require(rep_rc10_good["pass"], f"expected rc.10 \\ddagger and clean figure script to pass: {rep_rc10_good}")

        bad_fig_py = root / "bad_fig.py"
        bad_fig_py.write_text("import numpy as np\ny = x + np.random.normal(0, 0.02, size=len(x))\n", encoding="utf-8")
        rep_rc10_bad_fig = audit_docx.audit(rc10_out, expected_equations=1, figure_scripts=[bad_fig_py])
        require(
            rep_rc10_bad_fig["checks"]["no_synthetic_random_in_figure_scripts"] is False,
            "expected np.random.normal in validation figure script to fail no_synthetic_random_in_figure_scripts",
        )

        bad_jargon_doc = Document()
        bad_jargon_doc.add_paragraph("为了实现完全拉平起点的对照，我们补跑了5条轨迹。")
        bad_jargon_path = root / "rc10_bad_jargon.docx"
        bad_jargon_doc.save(bad_jargon_path)
        rep_bad_jargon = audit_docx.audit(bad_jargon_path)
        require(
            rep_bad_jargon["checks"]["no_residual_work_codes"] is False,
            "expected internal debugging jargon (完全拉平起点 / 补跑了) to fail no_residual_work_codes",
        )


        # Test rc.11 gates: inline OMML font-size/bold inheritance, Greek prefix space absorption, and table column consistency
        rc11_in = root / "rc11_inline_style_in.docx"
        rc11_out = root / "rc11_inline_style_out.docx"
        doc_rc11 = Document()
        tbl = doc_rc11.add_table(rows=1, cols=2)
        cell_p = tbl.cell(0, 0).paragraphs[0]
        r0 = cell_p.add_run(r"Metric {{OMML_INLINE: \Delta E + \langle\Delta E\rangle + \pi r}}")
        r0.font.size = native_math.Pt(8.5)
        r0.font.bold = True
        tbl.cell(0, 1).paragraphs[0].add_run("Value")
        doc_rc11.save(rc11_in)
        native_math.render_file(rc11_in, rc11_out)

        rep_rc11 = audit_docx.audit(rc11_out, expected_equations=1)
        require(rep_rc11["pass"], f"expected rc.11 inline styled table OMML to pass: {rep_rc11}")
        require(rep_rc11["checks"]["no_truncated_table_columns"] is True, "expected no_truncated_table_columns=True")

        with zipfile.ZipFile(rc11_out) as zf:
            xml_bytes = zf.read("word/document.xml")
        xml_root = audit_docx.etree.fromstring(xml_bytes)
        omath_text = "".join(xml_root.xpath(".//m:oMath//m:t/text()", namespaces=audit_docx.NAMESPACES))
        require(
            omath_text == "ΔE + ⟨ΔE⟩ + πr",
            f"expected Greek prefix trailing spaces to be absorbed ('ΔE + ⟨ΔE⟩ + πr'), got {omath_text!r}",
        )
        sz_vals = xml_root.xpath(".//m:oMath//m:r/w:rPr/w:sz/@w:val", namespaces=audit_docx.NAMESPACES)
        require(
            len(sz_vals) > 0 and all(v == "17" for v in sz_vals),
            f"expected inline m:r inside 8.5pt cell to inherit w:sz=17, got {sz_vals}",
        )

        # Test rc.12 gates: no_residual_template_placeholders and build_track_changes_docx XML inspector
        import build_track_changes_docx

        bad_tmpl_doc = Document()
        bad_tmpl_doc.add_paragraph("Deposition numbers xxxxxx contain the supplementary crystallographic data.")
        bad_tmpl_doc.add_paragraph("Insert text for Table of Contents here. ((Maximum 450 characters including spaces.))")
        bad_tmpl_path = root / "rc12_bad_template_placeholders.docx"
        bad_tmpl_doc.save(bad_tmpl_path)
        rep_bad_tmpl = audit_docx.audit(bad_tmpl_path)
        require(
            rep_bad_tmpl["checks"]["no_residual_template_placeholders"] is False,
            "expected residual publisher template placeholders (xxxxxx / Insert text for Table of Contents) to fail no_residual_template_placeholders",
        )
        require(
            rep_bad_tmpl["document"]["residual_template_placeholders"] == 2,
            f"expected 2 residual template placeholder hits, got {rep_bad_tmpl['document']['residual_template_placeholders']}",
        )

        tc_counts = build_track_changes_docx.inspect_xml_counts(rc11_out)
        require(tc_counts["equations"] == 1 and tc_counts["w_ins"] == 0, f"unexpected XML counts on clean rc11_out: {tc_counts}")

    print("scientific DOCX self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
