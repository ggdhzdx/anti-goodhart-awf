"""Ephemeral test-only authorities. Private keys never leave process memory."""
import base64
import copy
import json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from PIL import Image, ImageDraw
from design_contract import canonical, digest, file_digest
from design_scores import KNOWLEDGE, GROUPS, REDLINE_WEIGHTS, BOOLEAN_REDLINES, DIMENSIONS, PENALTIES
from design_capture_profile import CAPTURE_PROFILE, CSP_META, capture_frames


def complete_scores():
    return {'min_passing_score': 80.0,
            'optoelectronic_v3': {
                'category_a_knowledge_items': [{'id': key, 'weight': weight, 'clarity': 'S', 'visual_level': required, 'required_visual_level': required, 'is_ai_decorative_image': False} for key, (weight, required) in KNOWLEDGE.items()],
                'b_to_e_grades': {key: 'S' for group in GROUPS.values() for key in group},
                'redlines': {key: False if key in BOOLEAN_REDLINES else 0 for key in REDLINE_WEIGHTS}},
            'supermolecule_5dim': {**{key: maximum for key, (_, maximum) in DIMENSIONS.items()},
                                  'dim1_penalties': {key: False for key in [*PENALTIES, 'extreme_overload_or_unreadable']}}}


def sign(payload, private_key):
    return {'payload': copy.deepcopy(payload), 'signature': base64.b64encode(private_key.sign(canonical(payload))).decode()}


def save_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False), encoding='utf-8')


class EvidenceFixture:
    def __init__(self, directory, score_payload=None, html_text='<html><body>synthetic unit fixture</body></html>'):
        self.directory = Path(directory)
        self.directory.mkdir(exist_ok=True, parents=True)
        self.scores = copy.deepcopy(score_payload if score_payload is not None else complete_scores())
        self.html = self.directory / 'slide.html'
        self.png = self.directory / 'slide.png'
        html_text = html_text.replace("<script src='katex.min.js'></script>", '')
        if '<head>' in html_text:
            html_text = html_text.replace('<head>', '<head>' + CSP_META, 1)
        else:
            html_text = html_text.replace('<html>', '<html><head>' + CSP_META + '</head>', 1)
        self.html.write_text(html_text, encoding='utf-8')
        canvas = Image.new('RGB', (1920, 1080), 'white')
        ImageDraw.Draw(canvas).text((100, 100), 'SYNTHETIC UNIT FIXTURE - NOT A BROWSER RENDER', fill='black')
        canvas.save(self.png)
        self.renderer_key = Ed25519PrivateKey.generate()
        self.reviewer_key = Ed25519PrivateKey.generate()
        public = lambda key: base64.b64encode(key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)).decode()
        self.policy = {'schema_version': 1, 'renderers': {'fixture-renderer': public(self.renderer_key)}, 'reviewers': {'fixture-reviewer': public(self.reviewer_key)}}
        self.render = {'schema_version': 1, 'run_id': 'synthetic-run-001', 'renderer_id': 'fixture-renderer', 'renderer': 'Pillow synthetic unit fixture',
                       'artifacts': [{'artifact_id': 'slide-01', 'html_path': str(self.html), 'html_sha256': file_digest(self.html), 'png_path': str(self.png), 'png_sha256': file_digest(self.png), 'width': 1920, 'height': 1080, 'resources': []}]}
        self.render['capture_profile'] = CAPTURE_PROFILE
        self.render['artifacts'][0]['frame'] = capture_frames(self.html)[0]
        self.review = {'schema_version': 1, 'run_id': 'synthetic-run-001', 'reviewer_id': 'fixture-reviewer', 'render_payload_sha256': digest(self.render),
                       'score_payload_sha256': digest(self.scores), 'reviewed_artifact_ids': ['slide-01'], 'verdict': 'PASS', 'findings': []}
        criteria = set(KNOWLEDGE) | {key for group in GROUPS.values() for key in group} | set(DIMENSIONS)
        self.review['criterion_evidence'] = {key: {'artifact_ids': ['slide-01'], 'observation': 'Synthetic criterion observation for schema testing, not a scientific review'} for key in criteria}
        self.context = {'trust_policy_path': str(self.directory / 'test-only-trust.json'), 'manifest_path': str(self.directory / 'evidence.json'), 'expected_artifacts': {'slide-01': str(self.html)}, 'run_id': 'synthetic-run-001'}
        self.write()

    def write(self):
        self.review['render_payload_sha256'] = digest(self.render)
        save_json(self.context['trust_policy_path'], self.policy)
        save_json(self.context['manifest_path'], {'render': sign(self.render, self.renderer_key), 'review': sign(self.review, self.reviewer_key)})

    def attach(self, bundle):
        bundle['html_text'] = self.html.read_text(encoding='utf-8')
        bundle['dual_rubric_eval'] = self.scores
        bundle['blue_claimed_score'] = 100.0
        bundle['rendered_png_paths'] = [str(self.png)]
        bundle['red_critic_findings'] = []
        return bundle
