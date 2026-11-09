#!/usr/bin/env python3
"""
Generate a Microsoft Word DOCX with native Track Changes (<w:ins>/<w:del>) and optional
Right-Margin Rationale Comments (<w:comment>) by comparing an authoritative baseline DOCX
against a revised DOCX via an isolated Word COM instance, followed by automated AcceptAll()
zero-diff verification.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import tempfile
from typing import Any
import zipfile

from docx import Document
from lxml import etree


NAMESPACES = {
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
}


def inspect_xml_counts(docx_path: Path) -> dict[str, int]:
    """Count native OMML equations, drawings, Track Changes nodes, and comments in a DOCX archive."""
    with zipfile.ZipFile(docx_path) as zf:
        names = set(zf.namelist())
        doc_root = etree.fromstring(zf.read("word/document.xml"))
        comments_count = 0
        if "word/comments.xml" in names:
            c_root = etree.fromstring(zf.read("word/comments.xml"))
            comments_count = int(c_root.xpath("count(.//w:comment)", namespaces=NAMESPACES))
        return {
            "equations": int(doc_root.xpath("count(.//m:oMath)", namespaces=NAMESPACES)),
            "display_equations": int(doc_root.xpath("count(.//m:oMathPara)", namespaces=NAMESPACES)),
            "drawings": int(doc_root.xpath("count(.//w:drawing)", namespaces=NAMESPACES)),
            "w_ins": int(doc_root.xpath("count(.//w:ins)", namespaces=NAMESPACES)),
            "w_del": int(doc_root.xpath("count(.//w:del)", namespaces=NAMESPACES)),
            "comments": comments_count,
        }


def build_track_changes_docx(
    original_docx: Path,
    revised_docx: Path,
    output_docx: Path,
    author: str = "SciWord Peer-Review",
    initials: str = "PR",
    comments_spec: list[dict[str, Any]] | None = None,
    compare_formatting: bool = False,
    overwrite: bool = False,
) -> dict[str, Any]:
    """
    Create output_docx containing native Word Track Changes between original_docx and revised_docx,
    attach optional right-margin rationale comments, and verify 0-diff parity after AcceptAll().
    """
    original_docx = original_docx.expanduser().resolve()
    revised_docx = revised_docx.expanduser().resolve()
    output_docx = output_docx.expanduser().resolve()

    if not original_docx.is_file():
        raise FileNotFoundError(f"Original DOCX not found: {original_docx}")
    if not revised_docx.is_file():
        raise FileNotFoundError(f"Revised DOCX not found: {revised_docx}")
    if output_docx in (original_docx, revised_docx):
        raise ValueError("output_docx must differ from original_docx and revised_docx")
    if output_docx.exists() and not overwrite:
        raise FileExistsError(f"Refusing to overwrite existing file without --overwrite: {output_docx}")

    import win32com.client

    output_docx.parent.mkdir(parents=True, exist_ok=True)
    comments_added = 0
    unmatched_comments: list[str] = []

    with tempfile.TemporaryDirectory(prefix="sciword-track-changes-") as tmp_dir:
        tmp_root = Path(tmp_dir)
        tmp_orig = tmp_root / "orig.docx"
        tmp_rev = tmp_root / "rev.docx"
        tmp_out = tmp_root / "track_changes.docx"
        tmp_accepted = tmp_root / "accepted_verify.docx"

        shutil.copy2(original_docx, tmp_orig)
        shutil.copy2(revised_docx, tmp_rev)

        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        try:
            doc_orig = word.Documents.Open(str(tmp_orig), ReadOnly=True, AddToRecentFiles=False)
            doc_rev = word.Documents.Open(str(tmp_rev), ReadOnly=True, AddToRecentFiles=False)

            # wdCompareDestinationNew = 2, wdGranularityWordLevel = 1
            diff_doc = word.CompareDocuments(
                OriginalDocument=doc_orig,
                RevisedDocument=doc_rev,
                Destination=2,
                Granularity=1,
                CompareFormatting=bool(compare_formatting),
                CompareCaseChanges=True,
                CompareWhitespace=False,
                CompareTables=True,
                CompareHeaders=True,
                CompareFootnotes=True,
                CompareTextboxes=True,
                CompareFields=True,
                CompareComments=True,
                RevisedAuthor=author,
                IgnoreAllComparisonWarnings=True,
            )
            doc_orig.Close(SaveChanges=0)
            doc_rev.Close(SaveChanges=0)

            # Show revisions and comments in markup view
            diff_doc.TrackRevisions = True
            try:
                win = diff_doc.ActiveWindow
                win.View.ShowRevisionsAndComments = True
                win.View.RevisionsView = 0  # wdRevisionsViewFinal
            except Exception:
                pass

            # Attach optional right-margin comments
            if comments_spec:
                word.UserName = author
                word.UserInitials = initials
                p_count = diff_doc.Paragraphs.Count
                p_texts: list[tuple[int, str]] = []
                for idx in range(1, p_count + 1):
                    try:
                        t = diff_doc.Paragraphs(idx).Range.Text or ""
                    except Exception:
                        t = ""
                    p_texts.append((idx, t))

                for item in comments_spec:
                    c_text = str(item.get("text", "")).strip()
                    if not c_text:
                        continue
                    c_author = item.get("author")
                    c_initials = item.get("initials")
                    if c_author:
                        word.UserName = str(c_author)
                    if c_initials:
                        word.UserInitials = str(c_initials)

                    target_p_idx: int | None = item.get("paragraph_index")
                    match_sub = str(item.get("match", "")).strip()
                    matched_idx = None

                    if isinstance(target_p_idx, int) and 1 <= target_p_idx <= p_count:
                        matched_idx = target_p_idx
                    elif match_sub:
                        for p_i, p_t in p_texts:
                            if match_sub in p_t:
                                matched_idx = p_i
                                break

                    if matched_idx is not None:
                        rng = diff_doc.Paragraphs(matched_idx).Range
                        # Exclude trailing paragraph mark (\r) so the comment balloon anchors cleanly
                        if rng.End > rng.Start + 1:
                            rng.End = rng.End - 1
                        diff_doc.Comments.Add(Range=rng, Text=c_text)
                        comments_added += 1
                    else:
                        unmatched_comments.append(match_sub or f"paragraph_index={target_p_idx}")

            diff_doc.SaveAs2(str(tmp_out), FileFormat=16)  # wdFormatXMLDocument = 16
            diff_doc.Close(SaveChanges=0)

            # Verification pass: open tmp_out, AcceptAllRevisions + DeleteAllComments, save to tmp_accepted
            verify_doc = word.Documents.Open(str(tmp_out), ReadOnly=False, AddToRecentFiles=False)
            verify_doc.AcceptAllRevisions()
            if verify_doc.Comments.Count > 0:
                verify_doc.DeleteAllComments()
            verify_doc.TrackRevisions = False
            verify_doc.SaveAs2(str(tmp_accepted), FileFormat=16)
            verify_doc.Close(SaveChanges=0)
        finally:
            word.Quit(SaveChanges=0)

        shutil.copy2(tmp_out, output_docx)

        # Compare tmp_accepted against revised_docx
        doc_rev_py = Document(revised_docx)
        doc_acc_py = Document(tmp_accepted)

        rev_paras = [p.text.strip() for p in doc_rev_py.paragraphs if p.text.strip()]
        acc_paras = [p.text.strip() for p in doc_acc_py.paragraphs if p.text.strip()]
        para_diffs: list[str] = []
        if len(rev_paras) != len(acc_paras):
            para_diffs.append(f"non-empty paragraph count mismatch: revised={len(rev_paras)} vs accepted={len(acc_paras)}")
        for idx, (rp, ap) in enumerate(zip(rev_paras, acc_paras)):
            if rp != ap:
                para_diffs.append(f"P#{idx}: revised={rp[:60]!r} vs accepted={ap[:60]!r}")

        rev_counts = inspect_xml_counts(revised_docx)
        out_counts = inspect_xml_counts(output_docx)
        acc_counts = inspect_xml_counts(tmp_accepted)

    checks = {
        "has_track_changes_markup": (out_counts["w_ins"] + out_counts["w_del"]) > 0,
        "all_comments_anchored": len(unmatched_comments) == 0,
        "accepted_zero_text_diff": len(para_diffs) == 0,
        "accepted_equation_parity": acc_counts["equations"] == rev_counts["equations"],
        "accepted_drawing_parity": acc_counts["drawings"] == rev_counts["drawings"],
    }
    return {
        "pass": all(checks.values()),
        "checks": checks,
        "original_docx": str(original_docx),
        "revised_docx": str(revised_docx),
        "output_docx": str(output_docx),
        "track_changes_counts": out_counts,
        "revised_counts": rev_counts,
        "accepted_counts": acc_counts,
        "comments_added": comments_added,
        "unmatched_comments": unmatched_comments,
        "accepted_paragraph_diffs": para_diffs[:10],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original_docx", type=Path, help="Authoritative baseline DOCX")
    parser.add_argument("revised_docx", type=Path, help="Revised target DOCX")
    parser.add_argument("output_docx", type=Path, help="Output Track-Changes DOCX path")
    parser.add_argument("--author", default="SciWord Peer-Review", help="Author label for Track Changes and comments")
    parser.add_argument("--initials", default="PR", help="Author initials for comments")
    parser.add_argument("--comments-json", type=Path, help="Optional JSON file containing rationale comments list")
    parser.add_argument("--compare-formatting", action="store_true", help="Also track formatting changes")
    parser.add_argument("--overwrite", action="store_true", help="Allow overwriting output_docx if it exists")
    parser.add_argument("--json-out", type=Path, help="Optional path to write JSON verification report")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    comments_spec = None
    if args.comments_json:
        raw = json.loads(args.comments_json.expanduser().resolve().read_text(encoding="utf-8"))
        comments_spec = raw.get("comments", raw) if isinstance(raw, dict) else raw

    report = build_track_changes_docx(
        original_docx=args.original_docx,
        revised_docx=args.revised_docx,
        output_docx=args.output_docx,
        author=args.author,
        initials=args.initials,
        comments_spec=comments_spec,
        compare_formatting=args.compare_formatting,
        overwrite=args.overwrite,
    )
    payload = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    print(payload)
    if args.json_out:
        args.json_out.write_text(payload + "\n", encoding="utf-8")
    return 0 if report["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
