"""Validate and publish the Tutor / DesignAG / HTML-PPT immutable successors."""
import argparse
import copy
import datetime
import os
import pwd
import shutil
import subprocess
from release_hashes import canonical_hash, file_hash, paths, read, tree_hash, tree_v2, write
from stack_release_config import ROOT, REPORT, ENGINEERING, COMPONENTS, WORKFLOWS, PINS, SOURCES, LIMITATIONS, VERIFIER, updated, fingerprints
from validate_stack import validate


def freeze(path):
    entries = [p for p in paths(path) if not p.is_symlink()] if path.is_dir() else []
    subprocess.run(['chattr', '+i', *map(str, entries), str(path)], check=True)


def preflight():
    if os.geteuid() != 0:
        raise RuntimeError('Root is required for immutable release publication')
    registry = read(ROOT / 'registry.yaml')
    if (ROOT / 'bin/verify.py').resolve() != VERIFIER / 'verify.py':
        raise RuntimeError('Active verifier changed')
    guard = next(w for w in registry['workflows'] if w['id'] == 'anti-goodhart-verification')
    if guard['descriptor'] != 'workflows/anti-goodhart-verification/releases/3.7.0-rc.7/workflow.yaml':
        raise RuntimeError('Guard current changed')
    for name, (previous, version) in WORKFLOWS.items():
        workflow = next(w for w in registry['workflows'] if w['id'] == name)
        if workflow['descriptor'] != f'workflows/{name}/releases/{previous}/workflow.yaml' or version in workflow['releases']:
            raise RuntimeError('Workflow current changed or successor registered: ' + name)
        for filename in ('workflow.yaml', 'versions.lock'):
            if (ROOT / f'workflows/{name}/releases/{version}' / filename).exists():
                raise RuntimeError('Successor metadata already exists')
    descriptors = {}
    for name, (previous, version) in COMPONENTS.items():
        path = ROOT / f'components/skills/{name}/component.yaml'
        document = read(path)
        cid = f'skill.{name}'
        entry = next(c for c in registry['components'] if c['id'] == cid)
        if entry['latest_release'] != previous or registry['global_components'].get(cid, previous) != previous or version in document['releases']:
            raise RuntimeError('Component current changed or successor registered: ' + name)
        descriptors[name] = (path, document)
    evidence = read(REPORT / 'validation.json')
    if not evidence['passed'] or not all(evidence['checks'].values()) or evidence['sources'] != fingerprints():
        raise RuntimeError('Failed or stale validation')
    for step in evidence['steps'].values():
        for stream in ('stdout', 'stderr'):
            if file_hash(ROOT / step[stream]) != step[stream + '_sha256']:
                raise RuntimeError('Validation output changed')
    return registry, descriptors, evidence


def archive_evidence(evidence, stamp):
    archive = ROOT / f'reports/designag-evidence-validation-{stamp}'
    archive.mkdir()
    owner = pwd.getpwnam('zc')
    os.chown(archive, owner.pw_uid, owner.pw_gid)
    archived = copy.deepcopy(evidence)
    for step in archived['steps'].values():
        for stream in ('stdout', 'stderr'):
            original = ROOT / step[stream]
            destination = archive / original.name
            shutil.copy2(original, destination)
            step[stream] = str(destination.relative_to(ROOT))
    path = archive / 'validation.json'
    shutil.copytree(REPORT / 'browser-smoke', archive / 'browser-smoke')
    for entry in [archive / 'browser-smoke', *paths(archive / 'browser-smoke')]:
        os.chown(entry, owner.pw_uid, owner.pw_gid)
    write(path, archived, exclusive=True)
    return archive, path


def register_components(registry, descriptors, evidence_path):
    attestations = {}
    for name, (previous, version) in COMPONENTS.items():
        cid = f'skill.{name}'
        path, document = descriptors[name]
        source = SOURCES[name]
        meta = updated(copy.deepcopy(document['releases'][previous]))
        meta.update(observed_at='2026-11-10', source_snapshot=str(source.relative_to(ROOT)), tree_sha256=tree_hash(source),
                    provenance=f'D17/D18 evidence hardening; {evidence_path.relative_to(ROOT)} sha256={file_hash(evidence_path)}',
                    change_summary='Require complete fixed 15-criterion scoring and separately authorized, byte-bound, full-static-frame screenshot review; distinguish assembly from acceptance.')
        meta['capabilities'] += ['complete-fixed-rubric-without-default-grades', 'artifact-bound-authorized-render-and-review-evidence', 'explicit-draft-versus-final-acceptance']
        meta['limitations'] = LIMITATIONS
        meta['runtime_requirements'] += ['Pillow and cryptography (Ed25519) for DesignAG evidence validation; runner-owned public-key policy for final acceptance']
        document['releases'][version] = meta
        write(path, document)
        entry = next(c for c in registry['components'] if c['id'] == cid)
        entry.update(latest_release=version, descriptor_sha256=file_hash(path))
        if cid in registry['global_components']:
            registry['global_components'][cid] = version
        key = f'{cid}@{version}'
        registry['integrity_policy']['required_release_attestations'].append(key)
        entries = paths(source)
        attestations[key] = {'coverage': 'tree', 'descriptor': str(path.relative_to(ROOT)), 'descriptor_file_sha256': file_hash(path),
                             'entry_count': len(entries), 'legacy_tree_sha256': tree_hash(source), 'metadata_sha256': canonical_hash(meta),
                             'regular_file_bytes': sum(p.lstat().st_size for p in entries if p.is_file() and not p.is_symlink()),
                             'root': str(source.relative_to(ROOT)), 'symlink_count': sum(p.is_symlink() for p in entries), 'tree_sha256': tree_v2(source)}
    return attestations


def register_workflows(registry):
    new_files = []
    for name, (previous, version) in WORKFLOWS.items():
        workflow = next(w for w in registry['workflows'] if w['id'] == name)
        destination = ROOT / f'workflows/{name}/releases/{version}'
        destination.mkdir(parents=True, exist_ok=True)
        owner = pwd.getpwnam('zc')
        os.chown(destination, owner.pw_uid, owner.pw_gid)
        document = updated(read(ROOT / workflow['descriptor']))
        document.update(release=version, engineering_source=str(ENGINEERING.relative_to(ROOT)), engineering_source_tree_sha256=tree_hash(ENGINEERING), known_limitations=LIMITATIONS)
        if name == 'adaptive-interactive-tutor':
            document['engineering_gate'] = 'Split by cohesive responsibility; line counts are advisory unless explicitly bounded. Verify science with Guard 3.7.0-rc.7 and presentation evidence with DesignAG 1.0.0-rc.13 / HTML-PPT 1.0.0-rc.15. Structural assembly is not final acceptance; absent authorized review remains REVIEW_REQUIRED.'
        document['engineering_gate'] += ' Exact dependency files must exist; mixed releases fail closed. Preserve actual execution counts and matching upstream verification receipts.'
        document['scientific_gate'] += ' D17/D18 require complete fixed scoring and trusted byte-bound full-static-frame evidence; signature validity alone does not prove scientific correctness.'
        write(destination / 'workflow.yaml', document, exclusive=True)
        lock = read(ROOT / workflow['lock'])
        lock.update(workflow_release=version, locked_at='2026-11-10')
        lock['components'] = {cid: PINS.get(cid, release) for cid, release in lock['components'].items()}
        lock['components']['tool.awf-repository-verifier'] = '1.0.0-rc.2'
        write(destination / 'versions.lock', lock, exclusive=True)
        ref = {'descriptor': str((destination / 'workflow.yaml').relative_to(ROOT)), 'descriptor_sha256': file_hash(destination / 'workflow.yaml'),
               'lock': str((destination / 'versions.lock').relative_to(ROOT)), 'lock_sha256': file_hash(destination / 'versions.lock'), 'status': 'validated'}
        workflow.update(ref)
        workflow['releases'][version] = ref.copy()
        new_files.extend([destination / 'workflow.yaml', destination / 'versions.lock'])
    return new_files


def publish():
    registry, descriptors, evidence = preflight()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup = ROOT / f'backups/designag-evidence-{stamp}'
    backup.mkdir()
    owner = pwd.getpwnam('zc')
    os.chown(backup, owner.pw_uid, owner.pw_gid)
    shutil.copy2(ROOT / 'registry.yaml', backup / 'registry.yaml')
    for name, (path, _) in descriptors.items():
        shutil.copy2(path, backup / (name + '.yaml'))
    archive, evidence_path = archive_evidence(evidence, stamp)
    attestations = register_components(registry, descriptors, evidence_path)
    attestation = ROOT / f'attestations/release-integrity-designag-evidence-{stamp}.yaml'
    write(attestation, {'schema_version': 1, 'digest_contract': 'awf-tree-v2', 'observed_at': '2026-11-10', 'owner': 'designag-evidence-hardening',
                       'provenance': str(evidence_path.relative_to(ROOT)), 'releases': attestations}, exclusive=True)
    new_files = register_workflows(registry)
    registry['integrity_attestations'].append(str(attestation.relative_to(ROOT)))
    registry['integrity_policy']['required_release_attestations'].sort()
    owner = pwd.getpwnam('zc')
    for path in new_files:
        os.chown(path, owner.pw_uid, owner.pw_gid)
        subprocess.run(['runuser', '-u', 'zc', '--', 'test', '-r', str(path)], check=True)
    for path in [*SOURCES.values(), ENGINEERING, *new_files, archive, attestation]:
        freeze(path)
    # Switch public current pointers only after every new immutable unit is frozen.
    temporary = ROOT / 'registry.yaml.designag-evidence-new'
    write(temporary, registry, exclusive=True)
    os.replace(temporary, ROOT / 'registry.yaml')
    for path in [ROOT / 'registry.yaml', *[item[0] for item in descriptors.values()]]:
        os.chown(path, owner.pw_uid, owner.pw_gid)
    result = {'workflows': {name: version for name, (_, version) in WORKFLOWS.items()}, 'component_pins': PINS,
              'backup': str(backup), 'evidence': str(evidence_path), 'attestation': str(attestation)}
    write(REPORT / 'publication.json', result, exclusive=True)
    print(result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--validate-only', action='store_true')
    mode.add_argument('--publish', action='store_true')
    args = parser.parse_args()
    if args.validate_only:
        raise SystemExit(0 if validate() else 1)
    publish()
