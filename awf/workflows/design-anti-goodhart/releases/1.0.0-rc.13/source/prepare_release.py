"""Copy the current teaching stack into unregistered successor trees."""
from pathlib import Path
import shutil
ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'registry.yaml').is_file())
VERSIONS = {'design-anti-goodhart': ('1.0.0-rc.12', '1.0.0-rc.13'), 'html-ppt': ('1.0.0-rc.14', '1.0.0-rc.15'), 'adaptive-interactive-tutor': ('1.0.0-rc.25', '1.0.0-rc.26')}

for name, (old, new) in VERSIONS.items():
    base = ROOT / f'components/skills/{name}/releases'
    shutil.copytree(base / old / 'source', base / new / 'source')
    print(f'created {name}@{new}')
