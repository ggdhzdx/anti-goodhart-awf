"""AWF Guard: shape contracts."""
from __future__ import annotations

from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import Union
import ast
import numpy as np
from .errors import AtomicContractViolationError


def parse_jaxtyping_shape_spec(
    shape_spec: Union[str, Sequence[Union[str, int]]],
) -> Tuple[Union[str, int], ...]:
    """
    Parse either a `jaxtyping` space-separated dimension string (e.g. `"*batch N N+1"`,
    `"#batch rows=3 _"`, `"..."`, `""`) or a tuple/sequence of tokens (`("N", "N+1")`)
    into a normalized tuple of axis tokens.
    """
    if isinstance(shape_spec, str):
        s = shape_spec.strip()
        if not s:
            return ()
        raw_tokens: List[Union[str, int]] = s.split()
    else:
        raw_tokens = list(shape_spec)

    norm_tokens: List[Union[str, int]] = []
    variadic_seen = False
    for tok in raw_tokens:
        if isinstance(tok, int) and not isinstance(tok, bool):
            norm_tokens.append(tok)
            continue
        tok_s = str(tok).strip()
        if "," in tok_s and "(" not in tok_s:
            raise AtomicContractViolationError(
                f"[Jaxtyping Shape Syntax Error] Axes should be separated with spaces, not commas: `{tok_s}`"
            )
        if tok_s.endswith("#"):
            raise AtomicContractViolationError(
                f"[Jaxtyping Shape Syntax Error] Broadcastable axes must start with `#`, not end with `#`: `{tok_s}`"
            )
        is_var = tok_s == "..." or tok_s.startswith("*") or tok_s.startswith("#*")
        if is_var:
            if variadic_seen:
                raise AtomicContractViolationError(
                    f"[Jaxtyping Shape Syntax Error] Cannot use variadic specifiers (`*name` or `...`) more than once in `{shape_spec}`!"
                )
            variadic_seen = True
        norm_tokens.append(tok_s)
    return tuple(norm_tokens)


def safe_eval_symbolic_dim_expr(
    expr_str: str,
    symbolic_dims: Dict[str, int],
) -> int:
    """
    Safely evaluate a `jaxtyping` symbolic dimension algebra expression (e.g. `"N+1"`,
    `"N-1"`, `"2*N"`, `"N//2+1"`, `"M+N"`, `"min(M,N)"`, `"max(M,N)"`) via AST without raw `eval()`.
    """
    try:
        tree = ast.parse(expr_str, mode="eval")
    except SyntaxError as exc:
        raise AtomicContractViolationError(
            f"[Jaxtyping Symbolic Axis Syntax Error] Invalid symbolic dimension expression `{expr_str}`: {exc}"
        ) from exc

    def _eval_node(node: ast.AST) -> int:
        if isinstance(node, ast.Expression):
            return _eval_node(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, int) and not isinstance(node.value, bool):
            return int(node.value)
        if isinstance(node, ast.Name):
            if node.id not in symbolic_dims:
                raise AtomicContractViolationError(
                    f"[Jaxtyping Unbound Symbolic Axis] Cannot evaluate symbolic axis `{expr_str}` "
                    f"because dimension `{node.id}` has not been bound yet!"
                )
            return int(symbolic_dims[node.id])
        if isinstance(node, ast.UnaryOp):
            val = _eval_node(node.operand)
            if isinstance(node.op, ast.UAdd):
                return +val
            if isinstance(node.op, ast.USub):
                return -val
        if isinstance(node, ast.BinOp):
            left = _eval_node(node.left)
            right = _eval_node(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.FloorDiv):
                return left // right
            if isinstance(node.op, ast.Mod):
                return left % right
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            fn = node.func.id
            args = [_eval_node(a) for a in node.args]
            if fn == "min" and args:
                return min(args)
            if fn == "max" and args:
                return max(args)
            if fn == "abs" and len(args) == 1:
                return abs(args[0])
        raise AtomicContractViolationError(
            f"[Jaxtyping Unsupported Symbolic Axis] Disallowed AST construct in symbolic axis `{expr_str}`!"
        )

    return _eval_node(tree)


def _match_single_jaxtyping_axis(
    tok: Union[str, int],
    actual_dim: int,
    symbolic_dims: Dict[str, int],
    name: str,
    axis_idx: int,
    full_shape: Tuple[int, ...],
    atom_id: str,
    direction: str,
) -> None:
    """Match a single non-variadic axis token against `actual_dim` (`jaxtyping._check_dims`)."""
    if isinstance(tok, int):
        if actual_dim != tok:
            raise AtomicContractViolationError(
                f"[{atom_id} {direction} Shape Mismatch] `{name}` axis {axis_idx} expected "
                f"fixed size {tok}, got {actual_dim} (full shape {full_shape})!"
            )
        return

    s = str(tok).strip()
    broadcastable = False
    if s.startswith("#"):
        broadcastable = True
        s = s[1:]

    # Anonymous axis (`_` or `_foo`)
    if s == "_" or s.startswith("_"):
        return

    # Labeled fixed axis (`rows=3`)
    if s.count("=") == 1 and not any(op in s for op in ("==", "!=", "<=", ">=")):
        _, rhs = s.split("=", 1)
        s = rhs.strip()

    if broadcastable and actual_dim == 1:
        return

    # Fixed integer literal (`"3"` or `"#3"` or `"rows=3"`)
    try:
        fixed_sz = int(s)
    except ValueError:
        fixed_sz = None

    if fixed_sz is not None:
        if actual_dim != fixed_sz:
            raise AtomicContractViolationError(
                f"[{atom_id} {direction} Shape Mismatch] `{name}` axis {axis_idx} expected "
                f"fixed size {fixed_sz}, got {actual_dim} (full shape {full_shape})!"
            )
        return

    # Named identifier (`"N"`, `"#N"`)
    if s.isidentifier():
        if s in symbolic_dims:
            if symbolic_dims[s] != actual_dim:
                raise AtomicContractViolationError(
                    f"[{atom_id} {direction} Symbolic Shape Mismatch] `{name}` axis {axis_idx} "
                    f"symbolic dim `{s}` was bound to {symbolic_dims[s]}, but `{name}` "
                    f"has size {actual_dim} (full shape {full_shape})!"
                )
        else:
            symbolic_dims[s] = actual_dim
        return

    # Symbolic algebraic expression (`"N+1"`, `"N-1"`, `"2*N"`, `"M+N"`)
    expected_sz = safe_eval_symbolic_dim_expr(s, symbolic_dims)
    if actual_dim != expected_sz:
        raise AtomicContractViolationError(
            f"[{atom_id} {direction} Symbolic Algebraic Shape Mismatch] `{name}` axis {axis_idx} "
            f"expression `{s}` evaluated to {expected_sz} (given {symbolic_dims}), but `{name}` "
            f"has size {actual_dim} (full shape {full_shape})!"
        )


def check_jaxtyping_shape_contract(
    name: str,
    arr_shape: Tuple[int, ...],
    raw_spec_shape: Union[str, Sequence[Union[str, int]]],
    symbolic_dims: Dict[str, int],
    variadic_dims: Optional[Dict[str, Tuple[bool, Tuple[int, ...]]]] = None,
    atom_id: str = "ATOM",
    direction: str = "Input",
) -> None:
    """
    Validate `arr_shape` against `raw_spec_shape` supporting all `jaxtyping` features:
    - Fixed dimensions (`3`, `"rows=3"`), anonymous axes (`"_"`), broadcastable axes (`"#N"`, `"#3"`),
    - Named symbolic dimensions (`"N"`) and Algebraic symbolic dimensions (`"N+1"`, `"N-1"`, `"2*N"`, `"M+N"`),
    - Anonymous variadic batch dimensions (`"..."`) and Named/Broadcastable variadic batch dimensions
      (`"*batch"`, `"#*batch"` with `np.broadcast_shapes` verification),
    - Rollback of `symbolic_dims` and `variadic_dims` on failure.
    """
    tokens = parse_jaxtyping_shape_spec(raw_spec_shape)
    if variadic_dims is None:
        variadic_dims = {}

    sym_bak = symbolic_dims.copy()
    var_bak = variadic_dims.copy()
    try:
        var_indices = [
            i for i, t in enumerate(tokens)
            if isinstance(t, str) and (t == "..." or t.startswith("*") or t.startswith("#*"))
        ]
        if not var_indices:
            if len(tokens) != len(arr_shape):
                raise AtomicContractViolationError(
                    f"[{atom_id} {direction} Rank Mismatch] `{name}` expected shape {tokens} "
                    f"(ndim={len(tokens)}), but got actual shape {arr_shape} (ndim={len(arr_shape)})!"
                )
            for idx, (tok, act_d) in enumerate(zip(tokens, arr_shape)):
                _match_single_jaxtyping_axis(tok, act_d, symbolic_dims, name, idx, arr_shape, atom_id, direction)
            return

        i_var = var_indices[0]
        min_ndim = len(tokens) - 1
        if len(arr_shape) < min_ndim:
            raise AtomicContractViolationError(
                f"[{atom_id} {direction} Variadic Rank Mismatch] `{name}` has {len(arr_shape)} dimensions "
                f"(shape {arr_shape}), fewer than minimum {min_ndim} required by `{tokens}`!"
            )

        n_suffix = len(tokens) - i_var - 1
        j_end = len(arr_shape) - n_suffix

        # Prefix axes
        for idx in range(i_var):
            _match_single_jaxtyping_axis(tokens[idx], arr_shape[idx], symbolic_dims, name, idx, arr_shape, atom_id, direction)

        # Suffix axes
        for offset in range(n_suffix):
            tok_idx = i_var + 1 + offset
            arr_idx = j_end + offset
            _match_single_jaxtyping_axis(tokens[tok_idx], arr_shape[arr_idx], symbolic_dims, name, arr_idx, arr_shape, atom_id, direction)

        # Variadic middle slice
        var_tok = str(tokens[i_var])
        var_slice = arr_shape[i_var:j_end]
        if var_tok in ("...", "*_"):
            return

        var_bcast = False
        if var_tok.startswith("#*"):
            var_bcast = True
            var_name = var_tok[2:]
        else:
            var_name = var_tok[1:]

        if var_name not in variadic_dims:
            variadic_dims[var_name] = (var_bcast, var_slice)
        else:
            prev_bcast, prev_shape = variadic_dims[var_name]
            if prev_bcast or var_bcast:
                try:
                    bcast_shape = tuple(int(x) for x in np.broadcast_shapes(var_slice, prev_shape))
                except ValueError as exc:
                    raise AtomicContractViolationError(
                        f"[{atom_id} {direction} Variadic Broadcast Failure] `{name}` variadic batch "
                        f"`*{var_name}` has shape {var_slice}, which cannot broadcast with `{prev_shape}`!"
                    ) from exc
                if not prev_bcast and bcast_shape != prev_shape:
                    raise AtomicContractViolationError(
                        f"[{atom_id} {direction} Variadic Broadcast Direction Failure] `{name}` variadic "
                        f"`*{var_name}` shape {var_slice} cannot broadcast into fixed `{prev_shape}`!"
                    )
                if not var_bcast and bcast_shape != var_slice:
                    raise AtomicContractViolationError(
                        f"[{atom_id} {direction} Variadic Broadcast Direction Failure] Previous `*{var_name}` "
                        f"shape `{prev_shape}` cannot broadcast into non-broadcastable `{var_slice}`!"
                    )
                variadic_dims[var_name] = (prev_bcast and var_bcast, bcast_shape)
            else:
                if var_slice != prev_shape:
                    raise AtomicContractViolationError(
                        f"[{atom_id} {direction} Variadic Shape Mismatch] `{name}` variadic batch "
                        f"`*{var_name}` has shape {var_slice} != bound `{prev_shape}`!"
                    )
    except Exception:
        symbolic_dims.clear()
        symbolic_dims.update(sym_bak)
        variadic_dims.clear()
        variadic_dims.update(var_bak)
        raise
