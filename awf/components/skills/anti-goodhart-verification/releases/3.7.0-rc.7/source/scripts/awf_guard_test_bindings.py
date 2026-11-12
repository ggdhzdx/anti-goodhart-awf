"""Replace real function bindings across loaded modules in this release only."""
from pathlib import Path
import sys

SCRIPTS_ROOT = Path(__file__).resolve().parent


def replace_loaded_bindings(original, replacement):
    """Patch by object identity, including imported aliases; return a restoration log."""
    changes = []
    for module in list(sys.modules.values()):
        filename = getattr(module, "__file__", None)
        if not filename or not Path(filename).resolve().is_relative_to(SCRIPTS_ROOT):
            continue
        for name, value in list(vars(module).items()):
            if value is original:
                changes.append((module, name, value))
                setattr(module, name, replacement)
    return changes


def restore_bindings(changes):
    for module, name, original in reversed(changes):
        setattr(module, name, original)
