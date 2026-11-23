# Beyond-PDF Domain Background Synthesis & Zero-Bewilderment Onboarding Playbook (`skill.html-ppt@1.0.0-rc.16`)

## 1. Why Raw PDFs Leave Users Bewildered ("一头雾水")

Specialist research papers (*Nature*, *Science*, *Joule*, *JACS*, *Adv. Mater.*) are written for narrow sub-field reviewers who already build those exact devices or run those exact reactions every day. As a result, a raw PDF typically:
1. Skips **what the baseline device/system is and how it works** (zero schematic of a standard solar cell, OLED stack, battery cycle, or catalytic loop);
2. Drops **high-barrier sub-domain acronyms and metrics** in Paragraph 1 (`QFLS`, `WF`, `SFG`, `Edge-on`, `TTA`, `BCP/Ag`, `PDISNN`) without physical intuition or everyday analogies;
3. Jumps straight into **microscopic recipe differences** (`Method II vs Method III`, `Molecule A vs Molecule B`) before establishing why prior mainstream fixes hit a physical ceiling.

If the Agent merely summarizes or extracts what is printed inside the PDF, **all three channels—`Tutor (TDD)`, `GRILL`, and the generated `HTML-PPT` slides—plunge the user straight into unexplained jargon**.

**Core Mandate (Role 0 — `BackgroundSynthesizer & AudienceTranslator`)**:
Whenever raw inputs omit foundational context, you **MUST proactively synthesize world-knowledge background from outside the PDF** (`BEYOND_PDF_DOMAIN_KNOWLEDGE`) across a **4-Rung Zoom-In Funnel**, translate load-bearing jargon with concrete physical analogies, and draw custom `V2/V3` SVG/interactive schematics before touching the paper's specific recipe.

---

## 2. Dual-Source Provenance Rule (Synthesis Without Hallucination)

Separate every statement and visual element into two strict provenance classes:

| Provenance Class | Scope | Rule |
| :--- | :--- | :--- |
| **`BEYOND_PDF_DOMAIN_KNOWLEDGE`** | Macro industry stakes, canonical baseline working principle, thermodynamic/spin limits, plain-language physical analogies, mainstream prior-art trade-off deadlocks, custom SVG conceptual schematics | **Proactively synthesized by the Agent** from verified physics, chemistry, materials, and engineering principles—even when 0% of this tutorial context appears in the PDF. |
| **`PDF_PRIMARY_EVIDENCE`** | Paper-specific molecules/structures, sample names, experimental curves (`Fig. 1–6`), DFT/simulation numbers, champion vs. control metrics | **Strictly anchored to the PDF / `evidence_ingest_ledger`**. Never invent paper-specific experimental values or misattribute a conceptual SVG as an experimental paper figure. |

On slides that present synthesized background schematics, label conceptual diagrams transparently (e.g., `基础工作机理示意图 · 领域通用物理模型` rather than citing a non-existent `Fig. 0`).

---

## 3. Step 0.0: Omitted-Background Gap Audit & Turn-1 Plain-Language Primer

Before asking **any** Stage 0 Global Blueprint MCQs, Tutor questions, or Grill questions:

1. **Audit Omitted Foundations (`pdf_omitted_background_gaps`, $\ge 2$ items)**:
   Scan the PDF's Title, Abstract, and Introduction ¶1. List every foundational concept the authors silently assume the reader already knows:
   - *Device/System Architecture Gap*: What is the physical stack, reactor, or biological/computational pipeline? How does input energy/matter turn into output?
   - *Metric/Jargon Gap*: Which key quantities (`QFLS`, `Voc`, `FF`, `WF`, `EQE`, `overpotential`, `selectivity`) govern success, and what do they mean physically?
   - *Deadlock Gap*: Why can't engineers solve this problem with an obvious tweak?

2. **Deliver Turn-1 Plain-Language Onboarding Primer (`outside_pdf_onboarding_primer`)**:
   In your very first response to the user—**before** presenting Stage 0 blueprint choices or station questions—deliver a **3–5 sentence plain-language primer** that:
   - Names the real-world technology and why it matters;
   - Explains how the standard device/system works using a vivid everyday analogy;
   - Pinpoints where losses/failures happen and what single physical knob this paper turns to break the deadlock.

3. **Zero Internal Framework Codeword Leak Rule (Strictly Enforced by Gate `D13` & `D16`)**:
   **NEVER** expose internal AWF variable names, rubric codes, or mode flags to the user in chat dialogue, multiple-choice options, grill questions, or slide text!
   - **Forbidden leaks**: `V0`, `V1`, `V2`, `V3`, `V3动画`, `Stage k.1`, `Stage k.2`, `UNBOUNDED_FLOW_DRIVEN`, `JIT_DURING_QA`, `HYBRID_SEED_PLUS_JIT`, `AUTONOMOUS_DUAL_EVOLVE`, `gdd_grill_capsule`, `tdd_station_capsule`, `slide_manifest.json`.
   - **Plain human translations to use instead**:
     - Instead of *"是否配置 V3 交互动画 (JIT_DURING_QA)"* $\to$ say *"哪些核心难点需要做成**可拖动参数的交互式动态推演图**（推荐先顺着逻辑往下走，遇到抽象难点时我们再当场拍板加动态交互）"*.
     - Instead of *"页数策略 UNBOUNDED_FLOW_DRIVEN"* $\to$ say *"不人为硬凑或硬砍页数，顺着『背景铺垫 $\to$ 核心痛点 $\to$ 破局机理 $\to$ 实验铁证』把每一步讲透为止"*.

---

## 4. The 4-Rung Zoom-In Background Funnel (`four_rung_funnel`)

Every full-paper walkthrough ($\ge 10$ slides, or `is_full_paper_deck: true`) **MUST allocate $\ge 3$ dedicated opening background slides** (`background_slide_indices`, strictly `V2` or `V3` visual modality) marching from macro world knowledge down to the paper's entry point:

1. **Rung 1 — Macro Industry Stakes & Incumbent Ceiling (`rung1_macro_industry_stakes`)**:
   - Where is this technology used in the real world (grid photovoltaics, wearable power, OLED displays, green hydrogen, chip lithography), and what hard efficiency/lifetime/cost ceiling did the incumbent technology hit?
2. **Rung 2 — Canonical Baseline Working Principle (`rung2_canonical_working_principle` + `visual_schematic_plan`)**:
   - **Zero paper-specific molecules allowed yet!** Show how a *textbook baseline* device/cycle works from start to finish (e.g., photon absorption $\to$ exciton/carrier generation $\to$ selective transport layers $\to$ electrode collection).
3. **Rung 3 — Core Jargon Plain-Language Analogies & Definitions (`rung3_core_jargon_translations`, $\ge 2$ terms)**:
   - Every core term must carry three parts: `{term, plain_analogy, physical_meaning}`. Never define an obscure symbol solely with another obscure symbol.
4. **Rung 4 — Specific Bottleneck & Mainstream Prior-Art Deadlock (`rung4_prior_art_deadlock`)**:
   - Show *where* the standard process breaks down and *why* conventional fixes suffer a trade-off deadlock (e.g., insulating passivation plugs defects cleanly (`Voc` $\uparrow$) but blocks charge extraction (`FF` $\downarrow$)). End Rung 4 by formulating the exact design requirement that launches the paper's core strategy.

---

## 5. Four `V2 / V3` Visual Blueprints When the PDF Has ZERO Background Figures

Because raw PDFs rarely contain introductory schematics, Agents must **never** render background slides as `V0` bullet-point text cards. Use these four native HTML/SVG visual blueprints (`V2` or `V3`):

### Blueprint 1: Custom Inline SVG Canonical Stack / Cycle Cross-Section (`V2`)
- **Left / Center Canvas**: Hand-crafted crisp inline `<svg>` showing the canonical layered device (e.g., Glass / ITO / HTL / Perovskite / ETL / Metal) or catalytic/biological cycle with numbered causal badges `①` $\to$ `②` $\to$ `③` $\to$ `④` and directional electron ($e^-$) / hole ($h^+$) trajectories.
- **Right Column**: 2–3 concise causal cards matching badges `①–④` in plain physical language.

### Blueprint 2: Everyday Physical Analogy $\leftrightarrow$ Energy/Potential Landscape Bridge (`V2`)
- **Left Panel (Intuition Anchor)**: Clean SVG diagram of a tangible physical system—e.g., a hydroelectric dam reservoir drop (voltage potential vs.坝体漏水裂缝), or an escalator step mismatch at a station exit (interfacial energy barrier $\Delta \Phi$).
- **Right Panel (Scientific Formalism)**: Real energy-band / free-energy diagram (`E_vac`, `LUMO/HOMO` or `CB/VB`, `QFLS`) aligned horizontally with dashed mapping arrows linking each analogy element to its exact physical quantity.

### Blueprint 3: Interactive First-Principles Limit / Loss Sandbox (`V3`)
- **Interactive Widget**: HTML slider coupled to a real analytical equation (satisfying Gate `D15`)—for example, dragging **Interface Defect Density $N_t$** or **Cathode Work-Function Mismatch $\Delta \Phi$** to watch `QFLS` vs. external $V_{\text{OC}}$ split apart, or watching an `S`-shaped kink appear in real time on a simulated $J\text{–}V$ curve!

### Blueprint 4: Side-by-Side Prior-Art Trade-off Deadlock Schematic (`V2`)
- **2-Column Controlled Contrast**:
  - *Left SVG (`未修饰裸界面`)*: Thin interface $\to$ smooth carrier arrow (`FF` 高), but dense red trap pits eating carriers (`Voc` 低).
  - *Right SVG (`传统绝缘钝化层`)*: Trap pits plugged (`Voc` 高), but thick insulating wall reflects carriers back (`FF` 暴跌).
  - *Bottom Callout*: Crystallizes the exact design paradox ("既要填平缺陷坑洞，又要给电子修一座顺滑下坡桥") that motivates Slide $k+1$ (the paper's innovation).

---

## 6. Channel-Specific Onboarding Laws (`Tutor / TDD`, `GRILL`, `HTML-PPT`)

### A. `Tutor / TDD` Mode (`workflow_mode: "TDD"`)
- **Foundation-First Trunk 1**: Stations covering Rungs 1–4 (`is_background_station: true`) **must** record `beyond_pdf_background_synthesis` in `tdd_station_capsule`.
- **Ban Premature Paper-Recipe Quizzing**: Never ask about paper-specific material pairs (`BCP/Ag vs SnO2/Bi`, `PDISNN vs PDI2SNN`, `Method II vs Method III`) on Slide 1–3 before building the baseline working principle! Walk the Wittgenstein ladder from everyday analogy $\to$ baseline physical mechanism $\to$ paper problem.

### B. `GRILL` Mode (`workflow_mode: "GRILL"`)
- **Briefing-First Law (Never Grill in a Vacuum!)**: Raw PDFs didn't teach the background, so grilling the user cold on sub-field acronyms feels hostile and bewildering.
- On opening background stations, use `question_archetype: "FOUNDATION_INTUITION_BUILD"` (or `requires_beyond_pdf_background: true`) and **always deliver `background_briefing_anchor` FIRST** (3–5 sentences explaining the baseline system + plain-language analogy), followed by an intuitive first-principles reasoning question the user can genuinely deduce from that briefing!
  - *Bad Cold-Ambush Grill (Forbidden)*: *"论文对比了 PDISNN (Method III) 与 PDI2SNN 的 Edge-on 取向和 SFG 信号，请判断谁的功函数更低？"*
  - *Good Briefing-First Foundation Grill*:
    - **背景微导读 (`background_briefing_anchor`)**: *"有机太阳能电池像一块发电三明治：中间吸光层受光照后拆出『电子』和『空穴』，电子必须顺着能级台阶一路往下滑，才能顺利流进底部的阴极金属。但常见金属电极的『台阶高度（功函数）』往往太高，像一道反过来的上坡门槛挡在门口。"*
    - **直觉推演追问 (`grill_question`)**: *"【给定锚点】电子只能自发往能级更低的下游滑落；【冲突情境】如果阴极门口横着一道比吸光层还高的能级上坡门槛，且没有任何界面缓冲层；【一刀见血追问】跑到这里的大批电子会发生什么后果，最终反映在电池的电压和电流曲线上会变成什么样？"*

### C. `AUTONOMOUS_DUAL_EVOLVE` Mode (`workflow_mode: "AUTONOMOUS_DUAL_EVOLVE"`)
- Before initializing `slide_manifest.json`, populate `domain_background_bridge` inside `storyboard.json` and allocate $\ge 3$ opening `V2/V3` background slides with concrete scientific assertion titles (never generic labels like *"研究背景一"* or *"基本概念介绍"*—use concrete scientific titles such as *"五层钙钛矿光电三明治依靠选择性传输层分离电子与空穴"* or *"界面缺陷漏电与能级台阶错位共同卡死开路电压上限"*).

---

## 7. Cross-Domain Quick Reference Examples

| Sub-Domain Paper Topic | What Raw PDF Omits | Synthesized 4-Rung Background Runway (Slides 2–4) |
| :--- | :--- | :--- |
| **Inverted Perovskite Solar Cell Passivation** | How p-i-n stack works; what `QFLS` & non-radiative recombination mean | **S2 (Rung 1–2)**: Silicon 29.4% ceiling & custom SVG of 5-layer p-i-n stack turning photons into separated $e^-/h^+$. **S3 (Rung 3)**: Reservoir head-drop analogy $\leftrightarrow$ `QFLS` vs. external $V_{\text{OC}}$ loss diagram. **S4 (Rung 4)**: Why conventional alkylammonium passivation trades `Voc` gain against `FF` transport blockage. |
| **Organic Solar Cell Cathode Interlayer (`PDISNN`)** | Bulk-heterojunction exciton splitting; cathode work function (`WF`); why `S`-kinks happen | **S2 (Rung 1–2)**: Flexible/semitransparent OSC value + custom SVG of donor/acceptor exciton splitting & charge collection loop. **S3 (Rung 3)**: Escalator step-height analogy $\leftrightarrow$ electrode work function (`WF`) & interfacial dipole shift (`V3` interactive barrier slider). **S4 (Rung 4)**: Why `ZnO` photocatalytic instability & conventional organic interlayers' thickness sensitivity create an industrial roll-to-roll bottleneck. |
| **Blue PHOLED Polariton Anticrossing** | Spin statistics (25% singlet / 75% triplet); why microsecond triplet lifetime causes `TTA` burn-in | **S2 (Rung 1–2)**: OLED display energy bottleneck & 1:3 spin-statistics SVG funnel explaining fluorescent vs. phosphorescent OLEDs. **S3 (Rung 3)**: Crowded highway pile-up analogy $\leftrightarrow$ microsecond $\tau_T$ driving bimolecular `TTA` hot-exciton bond cleavage. **S4 (Rung 4)**: Why chemical heavy-atom tuning hits a color-purity vs. radiative-rate ceiling. |

---

## 8. Reference JSON Schema (`domain_background_bridge`)

Include inside `storyboard.json` (at `--init-storyboard`) or update via `--record-background-bridge`:

```json
{
  "pdf_omitted_background_gaps": [
    "原始 PDF 默认读者熟知有机太阳能电池体异质结吸光拆激子与双电极抽取闭环，未提供基础器件原理图",
    "原始 PDF 直接讨论阴极界面层功函数 WF、分子堆积取向与填充因子 FF，未解释高功函数势垒如何引发界面电荷堆积"
  ],
  "outside_pdf_onboarding_primer": "在进入论文的具体分子设计前，我们先用 1 分钟建立全局物理图景：有机太阳能电池是一块超薄柔性发电三明治，光照把中间活性层激发成电子和空穴，必须分头顺滑跑进正负极。但普通电极门口有一道『能级上坡门槛』，电子跨不过去就会堵在门口复合发热；这篇工作就是要设计一层超薄分子『下坡引桥』，既把门槛削平，又不怕涂厚。",
  "four_rung_funnel": {
    "rung1_macro_industry_stakes": "有机光伏兼具轻薄柔性与半透明发电优势，但大面积印刷器件受限于电极界面损耗而难以兼顾高效率与厚膜容忍度",
    "rung2_canonical_working_principle": {
      "summary": "给体/受体体异质结吸收光子产生激子并在界面拆分为自由电子与空穴，分别经阴极界面层 CIL 与阳极界面层选择性收集输出电能",
      "visual_schematic_plan": "手绘定制 SVG 五层有机光伏器件截面与激子拆分—载流子滑落闭环图（V2）"
    },
    "rung3_core_jargon_translations": [
      {
        "term": "电极功函数 (Work Function, WF)",
        "plain_analogy": "车站出口自动扶梯的台阶高度，台阶比地面低电子才能顺滑下楼出站",
        "physical_meaning": "把一个电子从电极费米能级移到真空能级所需的最小能量，决定阴极抽取电子是否存在势垒"
      },
      {
        "term": "界面偶极子 (Interfacial Dipole)",
        "plain_analogy": "在过高的门槛前铺设一段自带向下坡度的电动引桥",
        "physical_meaning": "界面极性分子有序排列产生的微观电场层，使真空能级发生突变从而有效下调电极功函数"
      }
    ],
    "rung4_prior_art_deadlock": "无机 ZnO 界面层易引发紫外光催化降解，而传统有机胺/苝酰亚胺界面层导电性弱、超过 10 nm 即严重阻断电流，陷入降势垒与厚膜导电的死结"
  },
  "background_slide_indices": [2, 3, 4],
  "paper_claims_strictly_from_pdf": true
}
```
