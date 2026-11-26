"""AWF Guard: formal chemical stoichiometry, spin-multiplicity parity, Wegscheider SMT & Feinberg CRNT gate."""
from __future__ import annotations

from collections import deque
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple
from rdkit import Chem
import sympy as sp
import z3

from awf_guard_numeric_contracts import finite_float as _finite_float
from awf_guard_numeric_contracts import finite_inputs as _finite_inputs

_MAX_WEGSCHEIDER_TOL = 1e-2


def _parse_species_entry(sp_name: str, spec: Dict[str, Any]) -> Tuple[Dict[str, int], int, int]:
    """Return `(element_counts, formal_charge, total_electrons)` from RDKit SMILES or explicit element map."""
    declared_charge = int(spec["charge"]) if "charge" in spec else 0
    if "smiles" in spec and spec["smiles"] is not None:
        mol_raw = Chem.MolFromSmiles(str(spec["smiles"]))
        if mol_raw is None:
            raise ValueError(f"RDKit rejected invalid SMILES for species `{sp_name}`: {spec['smiles']!r}")
        mol = Chem.AddHs(mol_raw)
        rdkit_charge = int(Chem.GetFormalCharge(mol))
        if "charge" in spec and rdkit_charge != declared_charge:
            raise ValueError(
                f"Species `{sp_name}` formal charge mismatch: SMILES has charge {rdkit_charge}, "
                f"declared charge is {declared_charge}"
            )
        charge = rdkit_charge
        elem_counts: Dict[str, int] = {}
        atomic_sum = 0
        for atom in mol.GetAtoms():
            sym = atom.GetSymbol()
            elem_counts[sym] = (elem_counts[sym] if sym in elem_counts else 0) + 1
            atomic_sum += int(atom.GetAtomicNum())
        return elem_counts, charge, atomic_sum - charge

    if "elements" in spec and isinstance(spec["elements"], dict) and spec["elements"]:
        ptable = Chem.GetPeriodicTable()
        elem_counts = {}
        atomic_sum = 0
        for sym_raw, cnt_raw in spec["elements"].items():
            sym = str(sym_raw)
            cnt = int(cnt_raw)
            if cnt < 0:
                raise ValueError(f"Negative atom count for `{sym}` in species `{sp_name}`")
            if cnt > 0:
                z_num = int(ptable.GetAtomicNumber(sym))
                if z_num <= 0:
                    raise ValueError(f"Unknown IUPAC element `{sym}` in species `{sp_name}`")
                elem_counts[sym] = cnt
                atomic_sum += z_num * cnt
        return elem_counts, declared_charge, atomic_sum - declared_charge

    raise ValueError(f"Species `{sp_name}` must specify either `smiles` or non-empty `elements` mapping")


def _complex_key(side_map: Dict[str, int]) -> Tuple[Tuple[str, int], ...]:
    return tuple(sorted((sp_id, coeff) for sp_id, coeff in side_map.items() if coeff != 0))


def _count_linkage_classes(edges: Sequence[Tuple[int, int]], n_nodes: int) -> int:
    adj: List[Set[int]] = [set() for _ in range(n_nodes)]
    for u_idx, v_idx in edges:
        adj[u_idx].add(v_idx)
        adj[v_idx].add(u_idx)
    seen: Set[int] = set()
    components = 0
    for start in range(n_nodes):
        if start not in seen:
            components += 1
            queue: deque[int] = deque([start])
            seen.add(start)
            while queue:
                curr = queue.popleft()
                for nxt in adj[curr]:
                    if nxt not in seen:
                        seen.add(nxt)
                        queue.append(nxt)
    return components


@_finite_inputs
def verify_stoichiometry_spin_and_wegscheider_smt(
    species_defs: Dict[str, Dict[str, Any]],
    reactions: Sequence[Dict[str, Any]],
    reaction_dg0: Sequence[float],
    reaction_barriers_fwd: Optional[Sequence[float]] = None,
    claims_oscillation_or_bistability: bool = False,
    is_weakly_reversible: bool = True,
    wegscheider_tol: float = 1e-4,
) -> Dict[str, Any]:
    """
    Formal Chemical Conservation, Electron-Spin Parity, Z3 Wegscheider Cycle-Closure SMT &
    Feinberg CRNT Deficiency Gate (`G5v`).
    """
    tol_f = _finite_float(wegscheider_tol)
    if not (0.0 < tol_f <= _MAX_WEGSCHEIDER_TOL):
        raise ValueError(f"G5v wegscheider_tol must be in (0, {_MAX_WEGSCHEIDER_TOL}], got {tol_f}")
    if not species_defs or not reactions or len(reaction_dg0) != len(reactions):
        raise ValueError("G5v requires non-empty species_defs, reactions, and matching reaction_dg0 length")
    if reaction_barriers_fwd is not None and len(reaction_barriers_fwd) != len(reactions):
        raise ValueError("reaction_barriers_fwd length must match reactions length")

    violations: List[str] = []
    species_order = list(species_defs.keys())
    sp_to_idx = {sp_id: idx for idx, sp_id in enumerate(species_order)}
    parsed_species: Dict[str, Tuple[Dict[str, int], int, int]] = {}
    all_elements: Set[str] = set()

    for sp_id in species_order:
        sp_spec = species_defs[sp_id]
        try:
            elems, charge, n_elec = _parse_species_entry(sp_id, sp_spec)
            parsed_species[sp_id] = (elems, charge, n_elec)
            all_elements.update(elems.keys())
            mult = int(sp_spec["spin_multiplicity"]) if "spin_multiplicity" in sp_spec else 1
            if mult < 1:
                violations.append(f"Species `{sp_id}` has invalid spin_multiplicity={mult} (< 1).")
            elif (n_elec % 2) != ((mult - 1) % 2):
                violations.append(
                    f"Electron-spin parity violation on `{sp_id}`: N_e={n_elec} incompatible with 2S+1={mult}."
                )
        except Exception as exc:
            violations.append(f"Species definition error for `{sp_id}`: {exc}")

    if violations:
        return {
            "status": "FAIL",
            "species_count": len(species_order),
            "reaction_count": len(reactions),
            "cycle_basis_count": 0,
            "crnt_deficiency": -1,
            "smt_status": "skipped_invalid_species",
            "unsat_core": [],
            "violations": violations,
        }

    elem_list = sorted(all_elements)
    n_sp = len(species_order)
    n_rxn = len(reactions)
    e_rows: List[List[int]] = []
    for el in elem_list:
        e_rows.append([parsed_species[sp_id][0][el] if el in parsed_species[sp_id][0] else 0 for sp_id in species_order])
    e_rows.append([parsed_species[sp_id][1] for sp_id in species_order])

    s_mat_int = [[0 for _ in range(n_rxn)] for _ in range(n_sp)]
    complex_to_id: Dict[Tuple[Tuple[str, int], ...], int] = {}
    rxn_edges: List[Tuple[int, int]] = []

    for r_idx, rxn in enumerate(reactions):
        stoich = rxn["stoich"] if "stoich" in rxn else {}
        if not isinstance(stoich, dict) or not stoich:
            violations.append(f"Reaction #{r_idx} has empty `stoich` map.")
            continue
        reactants: Dict[str, int] = {}
        products: Dict[str, int] = {}
        for sp_id, coeff_raw in stoich.items():
            if sp_id not in sp_to_idx:
                violations.append(f"Reaction #{r_idx} references undeclared species `{sp_id}`.")
                continue
            if isinstance(coeff_raw, bool) or int(coeff_raw) != coeff_raw:
                violations.append(f"Reaction #{r_idx} species `{sp_id}` coefficient {coeff_raw!r} must be exact integer.")
                continue
            coeff = int(coeff_raw)
            s_mat_int[sp_to_idx[sp_id]][r_idx] += coeff
            if coeff < 0:
                reactants[sp_id] = -coeff
            elif coeff > 0:
                products[sp_id] = coeff
        r_key = _complex_key(reactants)
        p_key = _complex_key(products)
        if not r_key or not p_key or r_key == p_key:
            violations.append(f"Reaction #{r_idx} must have distinct non-empty reactant and product complexes.")
        else:
            if r_key not in complex_to_id:
                complex_to_id[r_key] = len(complex_to_id)
            if p_key not in complex_to_id:
                complex_to_id[p_key] = len(complex_to_id)
            rxn_edges.append((complex_to_id[r_key], complex_to_id[p_key]))

    e_sym = sp.Matrix(e_rows)
    s_sym = sp.Matrix(s_mat_int)
    es_prod = e_sym * s_sym
    row_labels = [*elem_list, "net_charge"]
    for r_i in range(es_prod.rows):
        for c_j in range(es_prod.cols):
            imbalance = int(es_prod[r_i, c_j])
            if imbalance != 0:
                violations.append(
                    f"Stoichiometry/charge conservation violation (E*S != 0) at reaction #{c_j}, "
                    f"`{row_labels[r_i]}` net delta = {imbalance}"
                )

    stoich_rank = int(s_sym.rank())
    n_complexes = len(complex_to_id)
    n_linkage = _count_linkage_classes(rxn_edges, n_complexes) if n_complexes > 0 else 0
    deficiency = n_complexes - n_linkage - stoich_rank
    if claims_oscillation_or_bistability and deficiency == 0 and bool(is_weakly_reversible):
        violations.append(
            "Feinberg Deficiency-Zero Theorem violation: weakly reversible network with deficiency delta=0 "
            "cannot exhibit sustained mass-action oscillations or bistability."
        )

    cycle_basis = s_sym.nullspace()
    solver = z3.Solver()
    dg_vars = [z3.Real(f"dG_{r_idx}") for r_idx in range(n_rxn)]
    tol_rat = z3.RealVal(str(tol_f))
    for r_idx in range(n_rxn):
        dg_val = z3.RealVal(str(_finite_float(reaction_dg0[r_idx])))
        solver.assert_and_track(dg_vars[r_idx] >= dg_val - tol_rat, f"dg_lower_R{r_idx}")
        solver.assert_and_track(dg_vars[r_idx] <= dg_val + tol_rat, f"dg_upper_R{r_idx}")
        if reaction_barriers_fwd is not None:
            ea_var = z3.Real(f"Ea_fwd_{r_idx}")
            ea_val = z3.RealVal(str(_finite_float(reaction_barriers_fwd[r_idx])))
            solver.assert_and_track(ea_var == ea_val, f"ea_obs_R{r_idx}")
            solver.assert_and_track(ea_var >= -tol_rat, f"ea_fwd_nonneg_R{r_idx}")
            solver.assert_and_track(ea_var - dg_vars[r_idx] >= -tol_rat, f"ea_rev_nonneg_R{r_idx}")

    for c_idx, vec in enumerate(cycle_basis):
        lcm_denom = int(sp.ilcm(*[sp.Rational(vec[i]).q for i in range(n_rxn)]) if n_rxn > 1 else sp.Rational(vec[0]).q)
        int_coeffs = [int(sp.Rational(vec[i]) * lcm_denom) for i in range(n_rxn)]
        cycle_expr = z3.Sum([z3.RealVal(c_val) * dg_vars[i] for i, c_val in enumerate(int_coeffs) if c_val != 0])
        solver.assert_and_track(cycle_expr == z3.RealVal(0), f"wegscheider_cycle_{c_idx}")

    z3_verdict = solver.check()
    smt_status = str(z3_verdict)
    unsat_core_names: List[str] = []
    if z3_verdict != z3.sat:
        unsat_core_names = sorted(str(item) for item in solver.unsat_core())
        violations.append(
            f"Wegscheider / barrier thermodynamic SMT inconsistency ({smt_status}); unsat_core={unsat_core_names}"
        )

    return {
        "status": "PASS" if not violations else "FAIL",
        "species_count": n_sp,
        "reaction_count": n_rxn,
        "stoichiometric_rank": stoich_rank,
        "complex_count": n_complexes,
        "linkage_class_count": n_linkage,
        "crnt_deficiency": deficiency,
        "cycle_basis_count": len(cycle_basis),
        "smt_status": smt_status,
        "wegscheider_tolerance": tol_f,
        "unsat_core": unsat_core_names,
        "violations": violations,
    }
