"""
Dual-Pole Natural Academic Copywriting Guard (`skill.design-anti-goodhart@1.0.0-rc.25`).

Closes two complementary LLM slide-copywriting failure modes under low-density (`<= 260` char)
scientific presentation constraints (`Gate D3`):
1. Pole A — Coined Abstract Meta-Jargon & Predatory Metaphor Stacking:
   - Blocks coined `-ism` / `唯……论` strawmen (`证伪唯光吸收截面论`, `打破唯结晶度论`, `超越唯效率论`);
   - Blocks hyperbolic/predatory verb stacking (`借……收割整笼……`, `暴力收割`, `降维打击`, `一键解锁`).
2. Pole B — Pop-Science Sloganese, Rhetorical Contrast Clichés & Clickbait Triggers:
   - Blocks marketing contrast formulas (`不靠X也能Y`, `不必靠X：...就能...`, `不用X照样Y`);
   - Blocks sensationalist colon-hook titles (`颠覆认知：...`, `反直觉突破：...`, `四两拨千斤：...`);
   - Blocks clickbait interrogative `.detail-trigger` popover buttons (`+ 为什么吸光几乎不变`, `+ 凭什么...`);
   - Blocks colloquial anthropomorphic SVG `<text>` figure labels (`当捕能天线`, `充当搬运工`, `吃掉缺陷`).
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

COINED_ISM_AND_HYPERBOLE_PATTERNS = (
    r"(?:证伪|打破|颠覆|破除|终结|推翻|超越|告别)?唯[\u4e00-\u9fffA-Za-z0-9\-]{2,12}论",
    r"(?:借|凭|靠)[^，。；\n]{1,20}收割(?:整|全)",
    r"(?:暴力|疯狂)(?:收割|拉升|破解|碾压)",
    r"降维打击",
    r"一键解锁",
    r"弯道超车",
)

AI_SLOGANESE_CONTRAST_PATTERNS = (
    r"(?:不靠|不必靠|不用靠|无需靠)[^，。；\n]{1,18}(?:也能|照样|就能|即可|同样)",
    r"(?:不靠|不必靠|不用靠)[^：:，。\n]{1,16}[：:]",
    r"(?:颠覆(?:传统)?认知|打破(?:传统)?常识|反直觉突破|一招破解|四两拨千斤)\s*[：:]",
)

CLICKBAIT_TRIGGER_BUTTON_RE = re.compile(
    r"<button\b[^>]*class=[\"'][^\"']*\bdetail-trigger\b[^\"']*[\"'][^>]*>"
    r"\s*[+＋]?\s*(?:为什么|凭什么|到底怎么|揭秘|一文看懂)[^<]{1,24}</button>",
    flags=re.IGNORECASE | re.DOTALL,
)

COLLOQUIAL_SVG_ROLEPLAY_RE = re.compile(
    r"<text\b[^>]*>[^<]*(?:当捕能|充当搬运工|吃掉电子|吃掉空穴|吃掉缺陷|手拉手)[^<]*</text>",
    flags=re.IGNORECASE | re.DOTALL,
)


def scan_dual_pole_copywriting_text(label_prefix: str, text: str) -> Dict[str, List[str]]:
    """Scan plain slide text for both coined `-ism` jargon and pop-science contrast sloganese."""
    coined_hits: List[str] = []
    sloganese_hits: List[str] = []
    for pat in COINED_ISM_AND_HYPERBOLE_PATTERNS:
        match = re.search(pat, text)
        if match:
            coined_hits.append(
                f"{label_prefix}: coined meta-jargon / hyperbolic metaphor '{match.group(0)}' "
                "(state controlled baseline & physical mechanism directly)"
            )
    for pat in AI_SLOGANESE_CONTRAST_PATTERNS:
        match = re.search(pat, text)
        if match:
            sloganese_hits.append(
                f"{label_prefix}: pop-science contrast slogan '{match.group(0)}' "
                "(use calm declarative academic prose instead of '不靠X也能Y / 不必靠X：')"
            )
    return {
        "coined_ism_hits": coined_hits,
        "sloganese_hits": sloganese_hits,
    }


def scan_dual_pole_copywriting_html(html_text: str) -> Dict[str, Any]:
    """Inspect raw HTML for clickbait `.detail-trigger` labels and colloquial SVG `<text>` tags."""
    clickbait_triggers: List[str] = []
    colloquial_svg_labels: List[str] = []
    if not html_text.strip():
        return {
            "passed": True,
            "clickbait_triggers": clickbait_triggers,
            "colloquial_svg_labels": colloquial_svg_labels,
        }

    for match in CLICKBAIT_TRIGGER_BUTTON_RE.finditer(html_text):
        snippet = re.sub(r"<[^>]+>", "", match.group(0)).strip()
        clickbait_triggers.append(
            f"HTML detail-trigger '{snippet}': replace clickbait '为什么/凭什么/揭秘' label with concrete derivation or dataset name"
        )
    for match in COLLOQUIAL_SVG_ROLEPLAY_RE.finditer(html_text):
        snippet = re.sub(r"<[^>]+>", "", match.group(0)).strip()
        colloquial_svg_labels.append(
            f"SVG <text> '{snippet}': replace colloquial role-play phrasing with concise scientific label"
        )
    return {
        "passed": len(clickbait_triggers) == 0 and len(colloquial_svg_labels) == 0,
        "clickbait_triggers": clickbait_triggers,
        "colloquial_svg_labels": colloquial_svg_labels,
    }
