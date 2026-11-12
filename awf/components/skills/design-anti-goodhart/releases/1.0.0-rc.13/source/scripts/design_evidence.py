"""Verify artifact bytes and separately authorized renderer/reviewer signatures.

Trust policy is supplied by the runner, never taken from the submission bundle.
Signatures establish provenance, not the correctness of a human/agent judgment.
"""
import base64
import hashlib
import io
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from PIL import Image
from design_contract import CANVAS_SIZE, canonical, digest, file_bytes, file_digest, read_json, require
from design_scores import KNOWLEDGE, GROUPS, DIMENSIONS
from design_capture_profile import CAPTURE_PROFILE, capture_frames


class ReviewRequired(ValueError):
    """A caller has not supplied trusted review evidence."""


def _signature(envelope, authorities, identity_key):
    payload = envelope['payload']
    require(type(payload['schema_version']) is int and payload['schema_version'] == 1, 'Unknown evidence schema')
    identity = payload[identity_key]
    require(isinstance(identity, str) and identity in authorities, 'Unknown signing authority')
    public_bytes = base64.b64decode(authorities[identity], validate=True)
    key = Ed25519PublicKey.from_public_bytes(public_bytes)
    key.verify(base64.b64decode(envelope['signature'], validate=True), canonical(payload))
    return payload, public_bytes


def _artifacts(rows, expected):
    require(isinstance(rows, list) and rows and isinstance(expected, dict) and expected, 'Nonempty expected artifacts and render rows required')
    seen, png_paths, hashes, frames_by_source, image_hashes = set(), [], {}, {}, set()
    for row in rows:
        identity = row['artifact_id']
        require(identity in expected and identity not in seen, 'Unexpected or duplicate artifact')
        seen.add(identity)
        html = Path(row['html_path']).resolve()
        require(html == Path(expected[identity]).resolve(), 'Rendered artifact differs from the runner target')
        require(file_digest(html) == row['html_sha256'], 'HTML changed since rendering')
        frame = row['frame']
        expected_frames = capture_frames(html)
        require(frame in expected_frames and type(frame['index']) is int, 'Unknown captured slide/state')
        captured = frames_by_source.setdefault(str(html), [])
        require(frame not in captured, 'Captured frame repeated under another artifact ID')
        captured.append(frame)
        png = Path(row['png_path']).resolve()
        data = file_bytes(png)
        require(hashlib.sha256(data).hexdigest() == row['png_sha256'], 'Screenshot changed since rendering')
        if row['png_sha256'] in image_hashes:
            raise ReviewRequired('Identical screenshots across separate frames require additional review; do not reuse evidence')
        image_hashes.add(row['png_sha256'])
        with Image.open(io.BytesIO(data)) as im:
            require(im.format == 'PNG' and im.size == CANVAS_SIZE, 'Expected a real 1920x1080 PNG')
            im.verify()
        with Image.open(io.BytesIO(data)) as im:
            im.load()
        require(row['width'] == CANVAS_SIZE[0] and row['height'] == CANVAS_SIZE[1], 'Claimed screenshot dimensions mismatch')
        resources = row['resources']
        require(resources == [], 'This profile requires resources embedded into the signed HTML bytes')
        png_paths.append(str(png))
        hashes[identity] = {'html_sha256': row['html_sha256'], 'png_sha256': row['png_sha256']}
    require(seen == set(expected), 'Some target artifacts were never rendered')
    for html_path, captured in frames_by_source.items():
        require(len(captured) == len(capture_frames(html_path)), 'Not every static slide initial state was captured')
    require(len(set(png_paths)) == len(png_paths), 'One screenshot path reused for multiple artifacts')
    return png_paths, hashes


def verify_review(context, score_payload):
    if not context:
        raise ReviewRequired('Supply a runner-owned trust policy, run ID, expected artifacts and signed render/review receipts')
    policy = read_json(context['trust_policy_path'])
    require(policy['schema_version'] == 1, 'Unknown trust policy schema')
    package = read_json(context['manifest_path'])
    render, render_key = _signature(package['render'], policy['renderers'], 'renderer_id')
    require(render['capture_profile'] == CAPTURE_PROFILE, 'Unsupported capture profile')
    review, review_key = _signature(package['review'], policy['reviewers'], 'reviewer_id')
    require(render_key != review_key and render['renderer_id'] != review['reviewer_id'], 'Renderer and reviewer must be separately authorized')
    run_id = context['run_id']
    require(isinstance(run_id, str) and bool(run_id.strip()), 'Runner must provide a nonempty run ID')
    require(render['run_id'] == review['run_id'] == run_id, 'Evidence replayed from another run')
    require(isinstance(render['renderer'], str) and bool(render['renderer'].strip()), 'Missing renderer identity/version')
    require(review['render_payload_sha256'] == digest(render), 'Review is not bound to this render receipt')
    require(review['score_payload_sha256'] == digest(score_payload), 'Scores changed after review')
    png_paths, hashes = _artifacts(render['artifacts'], context['expected_artifacts'])
    reviewed = review['reviewed_artifact_ids']
    require(isinstance(reviewed, list) and len(reviewed) == len(set(reviewed)) and set(reviewed) == set(hashes), 'Review coverage differs from target artifacts')
    criteria = set(KNOWLEDGE) | {key for group in GROUPS.values() for key in group} | set(DIMENSIONS)
    observations = review['criterion_evidence']
    require(isinstance(observations, dict) and set(observations) == criteria, 'Every scored criterion needs a signed observation')
    cited_artifacts = set()
    for observation in observations.values():
        require(isinstance(observation['observation'], str) and bool(observation['observation'].strip()), 'Empty criterion observation')
        references = observation['artifact_ids']
        require(isinstance(references, list) and bool(references) and set(references) <= set(hashes), 'Criterion cites missing artifacts')
        cited_artifacts.update(references)
    require(cited_artifacts == set(hashes), 'Some reviewed artifacts have no criterion observations')
    findings = review['findings']
    require(isinstance(findings, list), 'Findings must be an explicit list')
    require(review['verdict'] in ('PASS', 'FAIL'), 'Review must have an explicit verdict')
    require(review['verdict'] == 'PASS' and not findings, 'Reviewer rejected the presentation or reported unresolved findings')
    return {'status': 'PASS', 'renderer_id': render['renderer_id'], 'reviewer_id': review['reviewer_id'],
            'run_id': run_id, 'render_payload_sha256': digest(render), 'review_payload_sha256': digest(review),
            'score_payload_sha256': digest(score_payload), 'artifacts': hashes, 'png_paths': png_paths,
            'assurance_scope': 'byte_integrity_and_authorized_attestation_not_independent_truth_proof'}
