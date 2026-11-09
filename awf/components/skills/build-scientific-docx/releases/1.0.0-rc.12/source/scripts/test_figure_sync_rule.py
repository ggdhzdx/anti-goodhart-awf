#!/usr/bin/env python3
"""Lightweight test to assert figure synchronization, multi-panel plot-box 0.0 px alignment, 4-way visual readback, table pipe safety, and 1:1 print-scale typography rules exist in SKILL.md and docx-equations-and-preservation.md."""

from __future__ import annotations

import sys
from pathlib import Path

REQUIRED_RULE_EXACT = (
    "当正文的研究方法、模型、参数、数据范围、结论、命名或版本改变时，"
    "交付 DOCX 前必须识别全部受影响图片并检查是否同步更新；"
    "逐一核对图内文字、面板顺序、模型名称、公式、颜色条和坐标范围、"
    "数值、图注、正文引用，防止旧合成图、旧缓存图和旧媒体对象被继承。"
)

RULE_KEYWORDS = [
    "研究方法、模型、参数、数据范围、结论、命名或版本改变",
    "受影响图片",
    "同步更新",
    "图内文字",
    "面板顺序",
    "模型名称",
    "颜色条和坐标范围",
    "正文引用",
    "旧合成图、旧缓存图和旧媒体对象被继承",
]

PRINT_SCALE_KEYWORDS = [
    "1:1 Print-Scale",
    "figsize",
    "mathtext.fontset",
]

PLOTBOX_AND_READBACK_KEYWORDS = [
    "0.0 px",
    "plot_box",
    "header band",
    "re.split(r\"\\s+\\|\\s+\"",
    "no_residual_latex_tokens",
    "no_residual_work_codes",
]


def test_skill_workflow(skill_path: Path) -> None:
    assert skill_path.is_file(), f"SKILL.md not found at {skill_path}"
    content = skill_path.read_text(encoding="utf-8")

    assert "## Required workflow" in content, "Required workflow section missing in SKILL.md"
    workflow_section = content.split("## Required workflow", 1)[1]

    assert REQUIRED_RULE_EXACT in workflow_section, (
        "Exact figure synchronization rule text missing from Required workflow in SKILL.md"
    )
    for kw in RULE_KEYWORDS:
        assert kw in workflow_section, (
            f"Keyword '{kw}' missing from Required workflow in SKILL.md"
        )
    for kw in PRINT_SCALE_KEYWORDS:
        assert kw in workflow_section, (
            f"Print-scale typography keyword '{kw}' missing from Required workflow in SKILL.md"
        )
    for kw in PLOTBOX_AND_READBACK_KEYWORDS:
        assert kw in workflow_section, (
            f"Plot-box/readback/pipe-safety keyword '{kw}' missing from Required workflow in SKILL.md"
        )


def test_preservation_checklist(ref_path: Path) -> None:
    assert ref_path.is_file(), f"Reference doc not found at {ref_path}"
    content = ref_path.read_text(encoding="utf-8")

    assert "## Preservation checklist" in content, (
        "Preservation checklist section missing in docx-equations-and-preservation.md"
    )
    checklist_section = content.split("## Preservation checklist", 1)[1]

    assert REQUIRED_RULE_EXACT in checklist_section, (
        "Exact figure synchronization rule text missing from Preservation checklist"
    )
    for kw in RULE_KEYWORDS:
        assert kw in checklist_section, (
            f"Keyword '{kw}' missing from Preservation checklist in docx-equations-and-preservation.md"
        )
    for kw in PRINT_SCALE_KEYWORDS:
        assert kw in content, (
            f"Print-scale typography keyword '{kw}' missing from docx-equations-and-preservation.md"
        )
    for kw in PLOTBOX_AND_READBACK_KEYWORDS:
        assert kw in content, (
            f"Plot-box/readback/pipe-safety keyword '{kw}' missing from docx-equations-and-preservation.md"
        )


def test_negative_detection() -> None:
    fake_content = "## Required workflow\n1. Some other rule"
    try:
        assert REQUIRED_RULE_EXACT in fake_content
    except AssertionError:
        pass
    else:
        raise AssertionError("Expected failure when rule text is missing")


def main() -> int:
    base_dir = Path(__file__).resolve().parent.parent
    skill_path = base_dir / "SKILL.md"
    ref_path = base_dir / "references" / "docx-equations-and-preservation.md"

    test_skill_workflow(skill_path)
    test_preservation_checklist(ref_path)
    test_negative_detection()

    print("PASS: Figure synchronization, plot-box 0.0 px alignment, 4-way visual readback, table pipe safety, and 1:1 print-scale typography rules verified in SKILL.md and docx-equations-and-preservation.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
