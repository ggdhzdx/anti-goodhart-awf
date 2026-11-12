"""One coordinated development unit with three immutable Workflow successors."""
from pathlib import Path
from release_hashes import tree_hash, tree_v2

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'registry.yaml').is_file())
ENGINEERING = Path(__file__).resolve().parent
REPORT = ROOT / 'reports/designag-evidence-hardening-20261110'
COMPONENTS = {
    'adaptive-interactive-tutor': ('1.0.0-rc.25', '1.0.0-rc.26'),
    'design-anti-goodhart': ('1.0.0-rc.12', '1.0.0-rc.13'),
    'html-ppt': ('1.0.0-rc.14', '1.0.0-rc.15'),
}
WORKFLOWS = {
    'adaptive-interactive-tutor': ('1.0.0-rc.25', '1.0.0-rc.26'),
    'design-anti-goodhart': ('1.0.0-rc.12', '1.0.0-rc.13'),
    'html-ppt': ('1.0.0-rc.11', '1.0.0-rc.12'),
}
PINS = {f'skill.{name}': version for name, (_, version) in COMPONENTS.items()}
PINS.update({'skill.anti-goodhart-verification': '3.7.0-rc.7', 'tool.awf-repository-verifier': '1.0.0-rc.2'})
SOURCES = {name: ROOT / f'components/skills/{name}/releases/{version}/source' for name, (_, version) in COMPONENTS.items()}
GUARD = ROOT / 'components/skills/anti-goodhart-verification/releases/3.7.0-rc.7/source'
VERIFIER = ROOT / 'components/tools/awf-repository-verifier/releases/1.0.0-rc.2/source'
LIMITATIONS = [
    'Integration tests use synthetic fixtures; actual decks still require rendered-page and scientific source review',
    'Trusted runner must own the public-key policy, expected artifacts and run ID; keys/trust are not provisioned by this package',
    'Separate signatures prove authorized attestation and byte binding, not scientific truth or reviewer independence of judgment',
    'Capture profile supports offline self-contained HTML static slide initial states; dynamic/generated views and interactions require separate assessment',
    'Remaining D1-D16 layout and scientific metadata are not all independently measured; only D17/D18 force-PASS mutations are tested here',
    'The fixed 15-criterion scientific knowledge rubric is the co-located optoelectronic rubric; other subjects require an explicit reviewed rubric successor',
    'Shared engineering closure is workflows/design-anti-goodhart/releases/1.0.0-rc.13/source and must accompany archives',
]


def updated(value):
    if isinstance(value, dict):
        return {key: updated(item) for key, item in value.items()}
    if isinstance(value, list):
        return [updated(item) for item in value]
    if isinstance(value, str):
        value = value.replace('3.7.0-rc.1', '3.7.0-rc.7').replace('73 automated gates', '14 slots / 74 subchecks').replace('73 gates', '14 slots / 74 subchecks')
        for name, (old, new) in COMPONENTS.items():
            value = value.replace(f'skill.{name}@{old}', f'skill.{name}@{new}')
    return value


def fingerprints():
    return {str(path.relative_to(ROOT)): {'legacy': tree_hash(path), 'v2': tree_v2(path)}
            for path in [*SOURCES.values(), ENGINEERING, GUARD, VERIFIER]}
