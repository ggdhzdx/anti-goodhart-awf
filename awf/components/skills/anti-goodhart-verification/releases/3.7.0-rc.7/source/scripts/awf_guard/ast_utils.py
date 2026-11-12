"""AWF Guard: ast utils."""
from __future__ import annotations

from typing import Any
from typing import Callable
import ast


def text_dedent(s: str) -> str:
    import textwrap
    return textwrap.dedent(s)


def _unwrap_target_fn(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Unwrap `@scientific_atom` wrapper to inspect underlying pure function AST/code object."""
    return getattr(fn, "__wrapped__", fn)


def _ast_structure_similarity(src_a: str, src_b: str) -> float:
    try:
        tree_a = ast.parse(text_dedent(src_a))
        tree_b = ast.parse(text_dedent(src_b))
    except SyntaxError:
        return 0.0
    seq_a = [type(n).__name__ for n in ast.walk(tree_a) if not isinstance(n, (ast.Load, ast.Store, ast.Name))]
    seq_b = [type(n).__name__ for n in ast.walk(tree_b) if not isinstance(n, (ast.Load, ast.Store, ast.Name))]
    if not seq_a or not seq_b:
        return 0.0
    bigrams_a = [f"{seq_a[i]}->{seq_a[i+1]}" for i in range(len(seq_a) - 1)]
    bigrams_b = [f"{seq_b[i]}->{seq_b[i+1]}" for i in range(len(seq_b) - 1)]
    if not bigrams_a or not bigrams_b:
        return 0.0
    set_a, set_b = set(bigrams_a), set(bigrams_b)
    return len(set_a & set_b) / max(len(set_a | set_b), 1)
