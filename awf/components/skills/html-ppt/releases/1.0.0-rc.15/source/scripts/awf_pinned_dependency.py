"""Load one exact co-located AWF dependency, rejecting absent or mixed versions."""
import importlib
from pathlib import Path
import sys


def dependency_scripts(component, release):
    root = Path(__file__).resolve().parents[7]
    scripts = root / "components/skills" / component / "releases" / release / "source/scripts"
    if not scripts.is_dir():
        raise FileNotFoundError(f"Required AWF dependency missing: {component}@{release}: {scripts}")
    return scripts


def load_exact(scripts, module_name, related_prefixes=()):
    scripts = scripts.resolve()
    expected = scripts / (module_name + ".py")
    if not expected.is_file():
        raise FileNotFoundError(f"Required AWF entry point missing: {expected}")
    for name, module in tuple(sys.modules.items()):
        if name == module_name or any(name.startswith(prefix) for prefix in related_prefixes):
            origin = getattr(module, "__file__", None)
            if origin is None or not Path(origin).resolve().is_relative_to(scripts):
                raise RuntimeError(f"Mixed AWF dependency in process: {name}: {origin}; expected {scripts}")
    if module_name in sys.modules:
        return sys.modules[module_name]
    original_path = list(sys.path)
    sys.path.insert(0, str(scripts))
    try:
        module = importlib.import_module(module_name)
        if Path(module.__file__).resolve() != expected:
            raise RuntimeError(f"Unexpected AWF module origin: {module.__file__}")
        return module
    finally:
        sys.path[:] = original_path
