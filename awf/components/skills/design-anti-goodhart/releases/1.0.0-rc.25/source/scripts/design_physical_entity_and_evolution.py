"""
Universal 5-Scale Physical-Entity Visual Fidelity, 4-Axis Orthogonal Exploration + Iterative Gen-1+
Evolutionary Image Tournament, and Two-Stage Text-Masked Blind Object-Recognition Audits
(`skill.design-anti-goodhart@1.0.0-rc.23`).

Closes three core visual Anti-Goodhart loopholes:
1. Prevents LLMs from substituting crude `<circle>`+`<line>` stick-doodles or flat blocks when
   depicting ANY real-world physical entity across five length scales (`ATOM_ORBITAL`,
   `MOLECULE_SUPRAMOLECULE`, `NANO_PHASE_MORPHOLOGY`, `DEVICE_EXPERIMENT`, `BIO_MACRO_SYSTEM`).
2. Prevents AI image-generation homogeneity ("all 4 samples look like minor style tweaks of one
   composition") via 4-Axis Orthogonal Gen-0 Exploration (`camera_topology`, `rendering_medium`,
   prompt Jaccard ceiling, and Pillow/NumPy 16x16 RGB distance) PLUS critique-guided `Gen-1+`
   iterative refinement with a monotonic quality ratchet.
3. Prevents multimodal critics from guessing crude shapes by reading nearby text labels ("看字猜图")
   via Stage A pure text-masked PNG blind object identification + Stage B full-slide alignment.
"""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

import numpy as np
from PIL import Image

from design_contract import require

PHYSICAL_ENTITY_SCALE_CLASSES = frozenset(
    {
        "ATOM_ORBITAL",
        "MOLECULE_SUPRAMOLECULE",
        "NANO_PHASE_MORPHOLOGY",
        "DEVICE_EXPERIMENT",
        "BIO_MACRO_SYSTEM",
    }
)

SANCTIONED_PHYSICAL_RENDER_ROUTES = frozenset(
    {
        "RDKIT_ACS_VECTOR",
        "PYMOL_3D_RENDER",
        "SHADED_25D_ENGINEERING_VECTOR",
        "EVOLUTIONARY_TEXTFREE_ILLUSTRATION_PLUS_SVG_CALLOUTS",
        "PRIMARY_PDF_FIGURE_CROP",
    }
)

ALLOWED_PHYSICAL_CRAFT_TIERS = frozenset(
    {
        "T2_SCIENTIFIC_STRUCTURAL_VECTOR",
        "T3_EDITORIAL_OR_3D_RENDER",
    }
)

KNOWN_CRAFT_TIERS = frozenset(
    {
        "T0_STICK_DOODLE",
        "T1_FLAT_ICON",
        "T2_SCIENTIFIC_STRUCTURAL_VECTOR",
        "T3_EDITORIAL_OR_3D_RENDER",
    }
)

VALID_RECOGNITION_CONFIDENCE = frozenset({"HIGH", "MEDIUM", "LOW_AMBIGUOUS_GEOMETRY"})

BLIND_ISOLATION_MODE = "READONLY_PNG_BLIND_SUBAGENT"

BARE_PRIMITIVE_MIN_SHAPES = 2
BARE_PRIMITIVE_MIN_LINES = 2
MIN_RICH_VECTOR_PATHS_OR_DEFS = 10
MIN_ENTITY_KEYWORD_LEN = 2

MIN_GEN0_CANDIDATES = 4
MIN_UNIQUE_GEN0_SHA = 4
MIN_DISTINCT_CAMERA_TOPOLOGIES = 3
MIN_DISTINCT_RENDERING_MEDIA = 3
MAX_PAIRWISE_PROMPT_JACCARD = 0.55
MIN_TOKEN_LEN_EN = 2
CJK_BIGRAM_WINDOW = 2
PIXEL_THUMB_SIZE = 16
PIXEL_NORM_DIVISOR = 255.0
MIN_MEAN_PAIRWISE_RGB_L1 = 0.10
MIN_PAIRWISE_RGB_L1 = 0.03
MIN_SHA_HEX_LEN = 16
MIN_CRITIQUE_PLAN_CHARS = 20
MIN_EVOLVED_GENERATION = 1
MIN_TOTAL_GENERATIONS_COMPLETED = 2

MIN_STAGE_A_PROMPT_CHARS = 30
MIN_OBJECT_DESC_CHARS = 8
MAX_SCORE_EMPTY_FALLBACK = -1.0

COACHING_PROMPT_FRAGMENTS = (
    r"直接(?:输出|给|打)\s*(?:PASS|通过)",
    r"默认合格",
    r"假装看不到",
    r"不要挑刺",
    r"all_pass\s*[:=]\s*true",
)


def _strip_hidden_dom_blocks(html_text: str) -> str:
    cleaned = re.sub(r"<head\b[^>]*>.*?</head>", " ", html_text, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"<script\b[^>]*>.*?</script>", " ", cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"<style\b[^>]*>.*?</style>", " ", cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"<template\b[^>]*>.*?</template>", " ", cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(
        r"<aside\b[^>]*class=[\"'][^\"']*\bnotes\b[^\"']*[\"'][^>]*>.*?</aside>",
        " ",
        cleaned,
        flags=re.DOTALL | re.IGNORECASE,
    )
    return cleaned


def _substantive_prompt_tokens(text: str) -> Set[str]:
    tokens: Set[str] = set()
    for tok in re.findall(r"[A-Za-z0-9_]+", text.lower()):
        if len(tok) >= MIN_TOKEN_LEN_EN:
            tokens.add(tok)
    for run in re.findall(r"[\u4e00-\u9fff]+", text):
        if len(run) >= CJK_BIGRAM_WINDOW:
            for idx in range(len(run) - CJK_BIGRAM_WINDOW + 1):
                tokens.add(run[idx : idx + CJK_BIGRAM_WINDOW])
    return tokens


def _compute_rgb_thumbnail_vector(img_path: Path) -> np.ndarray:
    with Image.open(img_path) as im:
        rgb = im.convert("RGB").resize((PIXEL_THUMB_SIZE, PIXEL_THUMB_SIZE), Image.Resampling.LANCZOS)
        arr = np.asarray(rgb, dtype=np.float32) / PIXEL_NORM_DIVISOR
    return arr.reshape(-1)


def _int_val(mapping: Dict[str, Any], key: str, fallback: int) -> int:
    val = mapping[key] if key in mapping and mapping[key] is not None else fallback
    return int(val)


def _float_val(mapping: Dict[str, Any], key: str, fallback: float) -> float:
    val = mapping[key] if key in mapping and mapping[key] is not None else fallback
    return float(val)


def _scan_svg_for_stick_doodles(html_text: str, has_declared_entities: bool) -> List[str]:
    issues: List[str] = []
    visible_dom = _strip_hidden_dom_blocks(html_text)
    svg_blocks = re.findall(r"<svg\b[^>]*>(.*?)</svg>", visible_dom, flags=re.DOTALL | re.IGNORECASE)
    if not svg_blocks:
        return issues

    for svg_idx, svg_body in enumerate(svg_blocks, start=1):
        g_blocks = re.findall(r"<g\b[^>]*>(.*?)</g>", svg_body, flags=re.DOTALL | re.IGNORECASE)
        for g_idx, g_body in enumerate(g_blocks, start=1):
            c_count = len(re.findall(r"<(?:circle|ellipse)\b", g_body, flags=re.IGNORECASE))
            l_count = len(re.findall(r"<line\b", g_body, flags=re.IGNORECASE))
            t_count = len(re.findall(r"<text\b", g_body, flags=re.IGNORECASE))
            p_count = len(re.findall(r"<(?:path|image)\b", g_body, flags=re.IGNORECASE))
            if (
                c_count >= BARE_PRIMITIVE_MIN_SHAPES
                and l_count >= BARE_PRIMITIVE_MIN_LINES
                and t_count == 0
                and p_count == 0
            ):
                issues.append(
                    f"UNLABELED_CRUDE_CIRCLE_LINE_CLUSTER: svg[{svg_idx}] <g[{g_idx}]> uses {c_count} bare "
                    "circles/ellipses + bare <line> sticks with zero <text> anchor or bezier/bitmap fidelity"
                )

        if has_declared_entities:
            img_count = len(re.findall(r"<image\b", svg_body, flags=re.IGNORECASE))
            external_img = len(re.findall(r"<img\b", visible_dom, flags=re.IGNORECASE))
            rich_count = len(
                re.findall(
                    r"<(?:path|linearGradient|radialGradient)\b",
                    svg_body,
                    flags=re.IGNORECASE,
                )
            )
            bare_shape_count = len(re.findall(r"<(?:circle|ellipse|rect)\b", svg_body, flags=re.IGNORECASE))
            bare_line_count = len(re.findall(r"<(?:line|polyline)\b", svg_body, flags=re.IGNORECASE))
            if (
                img_count == 0
                and external_img == 0
                and rich_count < MIN_RICH_VECTOR_PATHS_OR_DEFS
                and bare_shape_count >= BARE_PRIMITIVE_MIN_SHAPES
                and bare_line_count >= BARE_PRIMITIVE_MIN_LINES
            ):
                issues.append(
                    f"CRUDE_SVG_STICK_DOODLE_FOR_PHYSICAL_ENTITY: svg[{svg_idx}] depicts declared physical "
                    f"entities with only {rich_count} path/gradient primitives (< {MIN_RICH_VECTOR_PATHS_OR_DEFS}) "
                    "and bare shapes/lines instead of RDKit, 2.5D shaded engineering vectors, or evolutionary illustration"
                )
    return issues


def audit_physical_entity_visual_fidelity(
    html_text: str,
    visual_entity_manifest: Optional[Sequence[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Validate that every slide depicting physical entities across the 5 length scales uses a
    sanctioned high-craft rendering route rather than bare `<circle>`+`<line>` stick figures.
    """
    issues: List[str] = []
    manifest_items = list(visual_entity_manifest or [])
    for idx, item in enumerate(manifest_items, start=1):
        if not isinstance(item, dict):
            issues.append(f"Entity[{idx}] in visual_entity_manifest must be an object")
            continue
        eid = str(item.get("entity_id", f"entity_{idx}")).strip()
        sclass = str(item.get("scale_class", "")).strip().upper()
        route = str(item.get("render_route", "")).strip().upper()
        if sclass not in PHYSICAL_ENTITY_SCALE_CLASSES:
            issues.append(
                f"{eid}: unknown scale_class '{sclass}' (must be in {sorted(PHYSICAL_ENTITY_SCALE_CLASSES)})"
            )
        if route not in SANCTIONED_PHYSICAL_RENDER_ROUTES:
            issues.append(
                f"{eid}: unsanctioned physical render_route '{route}' "
                f"(allowed: {sorted(SANCTIONED_PHYSICAL_RENDER_ROUTES)})"
            )
        kws = item.get("expected_class_keywords")
        valid_kws = [
            str(k).strip()
            for k in (kws if isinstance(kws, list) else [])
            if len(str(k).strip()) >= MIN_ENTITY_KEYWORD_LEN
        ]
        if not valid_kws:
            issues.append(f"{eid}: missing non-empty `expected_class_keywords` for Stage A blind recognition")

    issues.extend(_scan_svg_for_stick_doodles(html_text, has_declared_entities=len(manifest_items) > 0))
    return {
        "gate": "D5_Physical_Entity_Visual_Fidelity_Audit",
        "passed": len(issues) == 0,
        "declared_entity_count": len(manifest_items),
        "issues": issues,
    }


def _check_gen0_diversity(
    gen0: Sequence[Any],
    check_disk_pixels: bool,
) -> Tuple[List[str], Dict[str, Dict[str, Any]], float, float, float]:
    issues: List[str] = []
    by_id: Dict[str, Dict[str, Any]] = {}
    shas: Set[str] = set()
    topologies: Set[str] = set()
    media: Set[str] = set()
    prompts: List[Tuple[str, Set[str]]] = []
    img_paths: List[Tuple[str, Path]] = []
    max_gen0_score = MAX_SCORE_EMPTY_FALLBACK
    max_jaccard = 0.0

    for idx, cand in enumerate(gen0, start=1):
        if not isinstance(cand, dict):
            issues.append(f"gen0_candidates[{idx}] must be an object")
            continue
        cid = str(cand.get("id", f"gen0_{idx}")).strip()
        by_id[cid] = cand
        sha = str(cand.get("sha256", "")).strip()
        if len(sha) < MIN_SHA_HEX_LEN:
            issues.append(f"Gen-0 '{cid}' missing valid sha256")
        else:
            shas.add(sha)
        topo = str(cand.get("camera_topology", "")).strip().upper()
        med = str(cand.get("rendering_medium", "")).strip().upper()
        if not topo:
            issues.append(f"Gen-0 '{cid}' missing camera_topology")
        else:
            topologies.add(topo)
        if not med:
            issues.append(f"Gen-0 '{cid}' missing rendering_medium")
        else:
            media.add(med)
        if cand.get("is_text_free") is not True:
            issues.append(f"Gen-0 '{cid}' must attest is_text_free=True")
        toks = _substantive_prompt_tokens(str(cand.get("prompt", "")))
        if not toks:
            issues.append(f"Gen-0 '{cid}' missing substantive prompt text")
        else:
            prompts.append((cid, toks))
        score_val = cand.get("score")
        if not isinstance(score_val, (int, float)) or isinstance(score_val, bool):
            issues.append(f"Gen-0 '{cid}' missing numeric rubric score")
        else:
            max_gen0_score = max(max_gen0_score, float(score_val))
        if check_disk_pixels:
            raw_path = Path(str(cand.get("path", "")))
            if not raw_path.is_file():
                issues.append(f"Gen-0 '{cid}' image file missing on disk: {raw_path}")
            else:
                img_paths.append((cid, raw_path))

    if len(shas) < MIN_UNIQUE_GEN0_SHA:
        issues.append(f"Gen-0 unique image SHA count {len(shas)} < {MIN_UNIQUE_GEN0_SHA} (duplicate/missing images)")
    if len(topologies) < MIN_DISTINCT_CAMERA_TOPOLOGIES:
        issues.append(
            f"Gen-0 camera_topology diversity {len(topologies)} < {MIN_DISTINCT_CAMERA_TOPOLOGIES}; "
            "paraphrasing one viewpoint causes severe visual homogeneity"
        )
    if len(media) < MIN_DISTINCT_RENDERING_MEDIA:
        issues.append(f"Gen-0 rendering_medium diversity {len(media)} < {MIN_DISTINCT_RENDERING_MEDIA}")

    for i in range(len(prompts)):
        for j in range(i + 1, len(prompts)):
            cid_a, toks_a = prompts[i]
            cid_b, toks_b = prompts[j]
            union = toks_a | toks_b
            jac = float(len(toks_a & toks_b)) / float(max(1, len(union)))
            max_jaccard = max(max_jaccard, jac)
            if jac > MAX_PAIRWISE_PROMPT_JACCARD:
                issues.append(
                    f"PROMPT_HOMOGENEITY_JACCARD_VIOLATION: Gen-0 '{cid_a}' vs '{cid_b}' "
                    f"prompt token Jaccard={jac:.3f} > {MAX_PAIRWISE_PROMPT_JACCARD:.2f}"
                )

    mean_l1 = 0.0
    min_l1 = 0.0
    if check_disk_pixels and len(img_paths) >= MIN_GEN0_CANDIDATES:
        vecs = [(cid, _compute_rgb_thumbnail_vector(p)) for cid, p in img_paths]
        dists: List[float] = []
        for i in range(len(vecs)):
            for j in range(i + 1, len(vecs)):
                dists.append(float(np.mean(np.abs(vecs[i][1] - vecs[j][1]))))
        if dists:
            mean_l1 = sum(dists) / float(len(dists))
            min_l1 = min(dists)
            if mean_l1 < MIN_MEAN_PAIRWISE_RGB_L1:
                issues.append(
                    f"IMAGE_PIXEL_HOMOGENEITY: mean pairwise 16x16 RGB L1={mean_l1:.4f} < {MIN_MEAN_PAIRWISE_RGB_L1:.2f}"
                )
            if min_l1 < MIN_PAIRWISE_RGB_L1:
                issues.append(
                    f"IMAGE_NEAR_DUPLICATE_CLONE: min pairwise 16x16 RGB L1={min_l1:.4f} < {MIN_PAIRWISE_RGB_L1:.2f}"
                )
    return issues, by_id, max_gen0_score, max_jaccard, mean_l1


def verify_evolutionary_image_tournament_ledger(
    ledger: Optional[Dict[str, Any]],
    *,
    check_disk_pixels: bool = False,
) -> Dict[str, Any]:
    """
    Enforce wide orthogonal Gen-0 image exploration (N>=4, >=3 camera topologies, >=3 media,
    low prompt Jaccard, pixel L1 diversity) plus critique-guided iterative refinement (`Gen-1+`)
    with monotonic score ratification.
    """
    if not isinstance(ledger, dict) or not ledger:
        return {"gate": "D5_Evolutionary_Image_Tournament", "passed": False, "issues": ["Missing evolutionary image tournament ledger"]}

    issues: List[str] = []
    gen0 = ledger.get("gen0_candidates")
    if not isinstance(gen0, list) or len(gen0) < MIN_GEN0_CANDIDATES:
        issues.append(f"gen0_candidates must contain at least {MIN_GEN0_CANDIDATES} orthogonal candidates")
        return {"gate": "D5_Evolutionary_Image_Tournament", "passed": False, "issues": issues}

    div_issues, by_id, max_gen0_score, max_jac, mean_l1 = _check_gen0_diversity(gen0, check_disk_pixels)
    issues.extend(div_issues)

    evolved = ledger.get("evolved_candidates")
    if not isinstance(evolved, list) or len(evolved) == 0:
        issues.append("EVOLUTION_MISSING_GEN1_REFINEMENT: at least 1 critique-guided evolved Gen-1+ candidate required")
    else:
        for idx, cand in enumerate(evolved, start=1):
            if not isinstance(cand, dict):
                issues.append(f"evolved_candidates[{idx}] must be an object")
                continue
            cid = str(cand.get("id", f"evo_{idx}")).strip()
            gen_num = _int_val(cand, "generation", 0)
            parent_id = str(cand.get("parent_candidate_id", "")).strip()
            plan_txt = str(cand.get("critique_and_edit_plan", "")).strip()
            sha = str(cand.get("sha256", "")).strip()
            if gen_num < MIN_EVOLVED_GENERATION:
                issues.append(f"Evolved '{cid}' generation={gen_num} < {MIN_EVOLVED_GENERATION}")
            if parent_id not in by_id:
                issues.append(f"Evolved '{cid}' references unknown parent_candidate_id='{parent_id}'")
            if len(plan_txt) < MIN_CRITIQUE_PLAN_CHARS:
                issues.append(f"Evolved '{cid}' critique_and_edit_plan too short (< {MIN_CRITIQUE_PLAN_CHARS} chars)")
            if len(sha) < MIN_SHA_HEX_LEN:
                issues.append(f"Evolved '{cid}' missing valid sha256")
            elif parent_id in by_id and sha == str(by_id[parent_id].get("sha256", "")).strip():
                issues.append(f"EVOLVED_IMAGE_UNCHANGED_CLONE: '{cid}' has identical SHA-256 to parent '{parent_id}'")
            if cand.get("is_text_free") is not True:
                issues.append(f"Evolved '{cid}' must attest is_text_free=True")
            score_val = cand.get("score")
            if not isinstance(score_val, (int, float)) or isinstance(score_val, bool):
                issues.append(f"Evolved '{cid}' missing numeric rubric score")
            if check_disk_pixels and not Path(str(cand.get("path", ""))).is_file():
                issues.append(f"Evolved '{cid}' image file missing on disk: {cand.get('path')}")
            by_id[cid] = cand

    if _int_val(ledger, "generations_completed", 0) < MIN_TOTAL_GENERATIONS_COMPLETED:
        issues.append(f"generations_completed must be >= {MIN_TOTAL_GENERATIONS_COMPLETED} (Gen-0 + Gen-1+)")
    if ledger.get("is_text_free_base") is not True:
        issues.append("Base raster illustration must declare `is_text_free_base=True` (all labels via crisp vector layer)")
    if ledger.get("has_vector_callout_overlay") is not True:
        issues.append("Evolutionary raster illustration must pair with a crisp vector callout overlay (`has_vector_callout_overlay=True`)")

    winner_id = str(ledger.get("winner_id", "")).strip()
    if winner_id not in by_id:
        issues.append(f"winner_id='{winner_id}' not found in Gen-0 / Evolved candidates")
    else:
        win_score = _float_val(by_id[winner_id], "score", MAX_SCORE_EMPTY_FALLBACK)
        all_max = max(
            (_float_val(c, "score", MAX_SCORE_EMPTY_FALLBACK) for c in by_id.values()),
            default=MAX_SCORE_EMPTY_FALLBACK,
        )
        if win_score < max_gen0_score or win_score < all_max:
            issues.append(
                f"MONOTONIC_RATCHET_VIOLATION: winner '{winner_id}' score={win_score:.2f} < best candidate score={all_max:.2f}"
            )

    return {
        "gate": "D5_Evolutionary_Image_Tournament",
        "passed": len(issues) == 0,
        "gen0_count": len(gen0),
        "evolved_count": len(evolved) if isinstance(evolved, list) else 0,
        "max_pairwise_prompt_jaccard": round(max_jac, 4),
        "mean_pairwise_rgb_l1": round(mean_l1, 4),
        "issues": issues,
    }


def verify_two_stage_blind_object_recognition(
    blind_obj_audit: Optional[Dict[str, Any]],
    visual_entity_manifest: Optional[Sequence[Dict[str, Any]]],
) -> Dict[str, Any]:
    """
    Enforce Stage A text-masked PNG blind object recognition + Stage B full-slide alignment check,
    eliminating text-guided hallucination ("看字猜图") and crude stick-figure physical entities.
    """
    if not isinstance(blind_obj_audit, dict) or not blind_obj_audit:
        return {
            "gate": "D18_Two_Stage_Masked_Blind_Object_Recognition",
            "passed": False,
            "issues": ["Missing two-stage text-masked blind object recognition audit receipt"],
        }
    issues: List[str] = []
    if str(blind_obj_audit.get("reviewer_isolation_mode", "")).strip() != BLIND_ISOLATION_MODE:
        issues.append(f"Invalid reviewer_isolation_mode (must be '{BLIND_ISOLATION_MODE}')")
    if (
        blind_obj_audit.get("saw_source_pdf") is not False
        or blind_obj_audit.get("saw_storyboard_json") is not False
        or blind_obj_audit.get("saw_speaker_notes") is not False
    ):
        issues.append("COLLUSION_CONTEXT_CONTAMINATION in two-stage blind object recognition")

    stage_a = blind_obj_audit.get("stage_a_masked_visual")
    stage_b = blind_obj_audit.get("stage_b_full_slide_check")
    if not isinstance(stage_a, dict) or not isinstance(stage_b, dict):
        issues.append("Both `stage_a_masked_visual` and `stage_b_full_slide_check` dicts are required")
        return {"gate": "D18_Two_Stage_Masked_Blind_Object_Recognition", "passed": False, "issues": issues}

    if stage_a.get("stage_a_all_text_hidden") is not True:
        issues.append("Stage A audit must confirm `stage_a_all_text_hidden=True`")
    masked_sha = str(stage_a.get("text_masked_png_sha256", "")).strip()
    full_sha = str(stage_b.get("full_slide_png_sha256", "")).strip()
    if len(masked_sha) < MIN_SHA_HEX_LEN or len(full_sha) < MIN_SHA_HEX_LEN:
        issues.append("Stage A & Stage B must bind valid PNG SHA-256 hashes")
    elif masked_sha == full_sha:
        issues.append("BLIND_MASKED_PNG_IDENTICAL_TO_UNMASKED: Stage A PNG cannot match full unmasked PNG")

    prompt_a = str(stage_a.get("stage_a_blind_prompt", "")).strip()
    if len(prompt_a) < MIN_STAGE_A_PROMPT_CHARS:
        issues.append(f"Stage A `stage_a_blind_prompt` too short (< {MIN_STAGE_A_PROMPT_CHARS} chars)")
    for pat in COACHING_PROMPT_FRAGMENTS:
        if re.search(pat, prompt_a, flags=re.IGNORECASE):
            issues.append(f"COLLUSION_PROMPT_COACHING in Stage A blind prompt: matches '{pat}'")

    unrec = stage_a.get("unrecognizable_crude_glyphs")
    if not isinstance(unrec, list):
        issues.append("Stage A missing `unrecognizable_crude_glyphs` list")
    elif len(unrec) > 0:
        issues.append(f"UNRECOGNIZABLE_CRUDE_GLYPH flagged by blind reader: {unrec}")

    rec_objs = stage_a.get("recognized_objects")
    if not isinstance(rec_objs, list) or len(rec_objs) == 0:
        issues.append("Stage A must contain non-empty `recognized_objects` list")
        rec_objs = []

    searchable_objects: List[Tuple[str, str]] = []
    for o_idx, obj in enumerate(rec_objs, start=1):
        if not isinstance(obj, dict):
            issues.append(f"Stage A recognized_objects[{o_idx}] must be a dict")
            continue
        desc = str(obj.get("visual_description", "")).strip()
        guess = str(obj.get("blind_guessed_object", "")).strip()
        conf = str(obj.get("recognition_confidence", "")).strip().upper()
        tier = str(obj.get("craft_tier", "")).strip()
        if len(desc) < MIN_OBJECT_DESC_CHARS:
            issues.append(f"Stage A object[{o_idx}] visual_description too short")
        if conf not in VALID_RECOGNITION_CONFIDENCE:
            issues.append(f"Stage A object[{o_idx}] invalid recognition_confidence '{conf}'")
        elif conf == "LOW_AMBIGUOUS_GEOMETRY":
            issues.append(f"UNRECOGNIZABLE_CRUDE_GLYPH: Stage A object[{o_idx}] '{guess or desc}' has LOW_AMBIGUOUS_GEOMETRY")
        if tier not in KNOWN_CRAFT_TIERS:
            issues.append(f"Stage A object[{o_idx}] invalid craft_tier '{tier}'")
        searchable_objects.append(((guess + " " + desc).lower(), tier))

    for e_idx, ent in enumerate(visual_entity_manifest or [], start=1):
        if not isinstance(ent, dict):
            continue
        eid = str(ent.get("entity_id", f"entity_{e_idx}")).strip()
        kws = [str(k).strip().lower() for k in (ent.get("expected_class_keywords") or []) if len(str(k).strip()) >= MIN_ENTITY_KEYWORD_LEN]
        for kw in kws:
            if kw in prompt_a.lower():
                issues.append(f"COLLUSION_BLIND_OBJECT_PROMPT_LEAK: Stage A prompt leaks keyword '{kw}' for '{eid}'")
                break
        matched_tiers = [tier for text_blob, tier in searchable_objects if any(kw in text_blob for kw in kws)]
        if kws and not matched_tiers:
            issues.append(
                f"BLIND_ENTITY_RECOGNITION_MISS: Stage A reader could not identify physical entity '{eid}' "
                f"(expected keywords {kws}) from text-masked visual PNG"
            )
        elif matched_tiers and not any(t in ALLOWED_PHYSICAL_CRAFT_TIERS for t in matched_tiers):
            issues.append(
                f"PHYSICAL_ENTITY_CRAFT_BELOW_FLOOR: physical entity '{eid}' rated {matched_tiers} "
                f"(must reach {sorted(ALLOWED_PHYSICAL_CRAFT_TIERS)})"
            )

    if stage_b.get("bitmap_pseudo_text_detected") is not False:
        issues.append("Stage B detected garbled AI pseudo-text/watermark inside bitmap artwork")
    misalign = stage_b.get("leader_line_misalignment_or_crossing")
    if not isinstance(misalign, list) or len(misalign) > 0:
        issues.append(f"Stage B reported leader-line misalignment or crossing: {misalign}")

    return {
        "gate": "D18_Two_Stage_Masked_Blind_Object_Recognition",
        "passed": len(issues) == 0,
        "recognized_object_count": len(searchable_objects),
        "issues": issues,
    }
