"""Add finite checks at callback return boundaries, retaining callback identity."""
import ast
from pathlib import Path

ENGINE = Path(__file__).with_name("awf_universal_anti_goodhart_gates.py")


def patch_callbacks():
    text = ENGINE.read_text()
    text = text.replace("from awf_guard_numeric_contracts import finite_array", "from awf_guard_numeric_contracts import finite_call as _finite_call, finite_array", 1)
    lines = text.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    edits = []
    for node in ast.walk(ast.parse(text)):
        if not isinstance(node, ast.Call):
            continue
        target = node.func
        if isinstance(target, ast.Name):
            selected = target.id.endswith("_fn") or target.id in {"fn", "oracle", "mutant"}
        elif isinstance(target, ast.Attribute):
            selected = target.attr.endswith("_fn")
        elif isinstance(target, ast.Subscript) and isinstance(target.slice, ast.Constant):
            selected = str(target.slice.value).endswith("_fn")
        else:
            selected = False
        line = lines[node.lineno - 1]
        if not selected or "np.nan" in line or "nan_res =" in line:
            continue
        begin = offsets[target.lineno - 1] + target.col_offset
        end = offsets[target.end_lineno - 1] + target.end_col_offset
        # Replace the callable and its opening parenthesis, without rewriting argument text.
        if text[end:end + 1] != "(":
            raise RuntimeError("Unsupported callback call formatting")
        source = text[begin:end]
        separator = "" if not node.args and not node.keywords else ", "
        edits.append((begin, end + 1, f"_finite_call({source}{separator}"))
    for begin, end, value in sorted(edits, reverse=True):
        text = text[:begin] + value + text[end:]
    ENGINE.write_text(text)


if __name__ == "__main__":
    patch_callbacks()
