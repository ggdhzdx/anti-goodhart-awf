"""Complete fixed-weight rubric arithmetic; never invent a missing assessment."""
from design_contract import MIN_PASS_SCORE, boolean, number, require

# One-to-one transcription of the co-located rubric's 15-row knowledge table.
KNOWLEDGE = {
    'A1_pholed': (2.0, 'V3'), 'A1_fluorescence_phosphorescence': (2.0, 'V3'),
    'A1_blue_lifetime': (1.0, 'V2'), 'A1_tpa_tta': (3.0, 'V3'),
    'A2_prior_art': (4.0, 'V2'), 'A3_purcell_near_field': (3.0, 'V3'),
    'A3_etl_spp': (3.0, 'V3'), 'A3_anticrossing': (4.0, 'V3'),
    'A3_eml_decay': (4.0, 'V3'), 'A4_device_evolution': (3.0, 'V3'),
    'A4_low_q': (2.0, 'V3'), 'A4_molecules': (2.0, 'V2'),
    'A5_depth': (8.0, 'V2'), 'A6_paired_baselines': (3.0, 'V2'),
    'A6_tradeoffs': (2.0, 'V2'),
}
GRADES = {'S': 1.0, 'A': 0.75, 'B': 0.50, 'C': 0.25, 'D': 0.0}
VISUAL = {'V0': 0.30, 'V1': 0.50, 'V2': 0.80, 'V3': 1.00}
GROUPS = {'B': {'B1': 4.0, 'B2': 5.0, 'B3': 7.0, 'B4': 4.0}, 'C': {'C1': 6.0, 'C2': 5.0, 'C3': 5.0}, 'D': {'D1': 5.0, 'D2': 3.0}, 'E': {'E1': 7.0, 'E2': 3.0}}
REDLINE_WEIGHTS = {'R1_latex_leak': 5.0, 'R2_broken_layout_pages': 2.0, 'R3_fake_or_misplaced_charts': 3.0, 'R4_ai_deco_mechanism_fakes': 2.0, 'R5_prompt_residue_hits': 2.0, 'R6_teleprompter_visible': 2.0, 'R7_scientific_fact_errors': 2.0}
BOOLEAN_REDLINES = {'R1_latex_leak', 'R6_teleprompter_visible'}
REDLINE_CAP = 15.0
DIMENSIONS = {'dim1_readability_base_25': ('dim1_readability_layout_25', 25.0), 'dim2_logic_score_20': ('dim2_narrative_logic_20', 20.0), 'dim3_richness_accuracy_20': ('dim3_richness_accuracy_20', 20.0), 'dim4_visual_fidelity_20': ('dim4_visual_fidelity_20', 20.0), 'dim5_interaction_15': ('dim5_interaction_design_15', 15.0)}
PENALTIES = {'top_heavy_imbalance': 6.0, 'bottom_overflow_clipped': 5.0, 'raw_latex_exposed': 6.0, 'too_few_slides_overload': 5.0, 'font_too_small': 5.0, 'text_overlap': 3.5, 'grid_3plus1_orphan': 3.0}
EXTREME_READABILITY_CAP = 2.0


def _knowledge(items):
    require(isinstance(items, list) and len(items) == len(KNOWLEDGE), 'All 15 canonical knowledge criteria are required')
    seen, breakdown, capped = set(), {}, []
    for item in items:
        key = item['id']
        require(key in KNOWLEDGE and key not in seen, 'Unknown or duplicate knowledge group')
        seen.add(key)
        weight, required = KNOWLEDGE[key]
        require(number(item['weight']) == weight and item['required_visual_level'] == required, 'Rubric weights/required visual levels are fixed')
        require(item['clarity'] in GRADES and item['visual_level'] in VISUAL, 'Unknown clarity or modality grade')
        visual = 'V0' if boolean(item['is_ai_decorative_image']) else item['visual_level']
        factor = 1.0 if VISUAL[visual] >= VISUAL[required] else VISUAL[visual]
        breakdown[key] = round(weight * GRADES[item['clarity']] * factor, 3)
        if visual == 'V0':
            capped.append(key)
    return breakdown, capped


def _redlines(redlines):
    require(isinstance(redlines, dict) and set(redlines) == set(REDLINE_WEIGHTS), 'Explicit R1-R7 assessment is required')
    total, count = 0.0, 0
    for key, weight in REDLINE_WEIGHTS.items():
        value = redlines[key]
        if key in BOOLEAN_REDLINES:
            value = int(boolean(value))
        else:
            require(type(value) is int and value >= 0, 'Redline counts must be nonnegative integers')
        count += value
        total += weight * value
    return min(REDLINE_CAP, total), count


def score_optoelectronic_rubric_v3(payload):
    breakdown, capped = _knowledge(payload['category_a_knowledge_items'])
    grades = payload['b_to_e_grades']
    require(isinstance(grades, dict) and set(grades) == {key for group in GROUPS.values() for key in group}, 'All B-E rubric grades are required')
    scores = {}
    for name, group in GROUPS.items():
        total = 0.0
        for key, weight in group.items():
            value = grades[key]
            if isinstance(value, str):
                require(value in GRADES, 'Unknown rubric grade')
                ratio = GRADES[value]
            else:
                ratio = number(value, high=1.0)
            total += weight * ratio
        scores[name] = round(total, 3)
    deduction, count = _redlines(payload['redlines'])
    a_score = sum(breakdown.values())
    gross = round(a_score + sum(scores.values()), 2)
    return {'rubric': 'optoelectronic_v3_100_plus_R15', 'A_scientific_explanation_46': a_score,
            'B_figures_and_evidence_20': scores['B'], 'C_expression_and_clarity_16': scores['C'],
            'D_visual_and_engineering_8': scores['D'], 'E_interaction_quality_10': scores['E'],
            'gross_score_100': gross, 'redline_deduction_capped_15': -deduction,
            'final_score': max(0.0, round(gross - deduction, 2)), 'redline_count': count,
            'v0_pure_text_capped_items': capped, 'a_item_breakdown': breakdown}


def score_supermolecule_5dim_rubric(payload):
    scores = {out: number(payload[key], high=maximum) for key, (out, maximum) in DIMENSIONS.items()}
    penalties = payload['dim1_penalties']
    require(isinstance(penalties, dict) and set(penalties) == set(PENALTIES) | {'extreme_overload_or_unreadable'}, 'Every readability penalty must be explicitly assessed')
    flags = {key: boolean(value) for key, value in penalties.items()}
    first = 'dim1_readability_layout_25'
    if flags['extreme_overload_or_unreadable']:
        scores[first] = min(scores[first], EXTREME_READABILITY_CAP)
    else:
        scores[first] = max(0.0, scores[first] - sum(weight for key, weight in PENALTIES.items() if flags[key]))
    return {'rubric': 'supermolecule_5dim_100', **scores, 'final_score': round(sum(scores.values()), 2)}


def calculate_scores(payload):
    require(isinstance(payload, dict), 'Rubric payload must be an object')
    threshold = number(payload['min_passing_score'], low=MIN_PASS_SCORE)
    optical = score_optoelectronic_rubric_v3(payload['optoelectronic_v3'])
    pedagogical = score_supermolecule_5dim_rubric(payload['supermolecule_5dim'])
    passed = optical['redline_count'] == 0 and min(optical['final_score'], pedagogical['final_score']) >= threshold
    return {'scores_passed': passed, 'optoelectronic_v3_result': optical, 'supermolecule_5dim_result': pedagogical}
