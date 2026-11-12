"""Windows Chrome smoke test. Test-only signer keys stay in process memory."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'registry.yaml').is_file())
SOURCE = ROOT / 'components/skills/design-anti-goodhart/releases/1.0.0-rc.13/source'
sys.path[:0] = [str(SOURCE / 'scripts'), str(SOURCE)]
from design_tests.evidence_fixtures import EvidenceFixture
from design_contract import file_digest
from design_tests.evidence_fixtures import save_json
from design_acceptance import evaluate_visual_red_blue_adversarial_audit

REPORT = ROOT / 'reports/designag-evidence-hardening-20261110/browser-smoke'
HTML = '''<!doctype html><html><head><meta charset="utf-8"><style>
*{box-sizing:border-box}body{margin:0;width:1920px;height:1080px;background:#f4f0e8;color:#123c40;font-family:Arial,sans-serif;padding:96px}
h1{font-size:76px;max-width:1300px;margin:24px 0 64px}p{font-size:32px;line-height:1.5}.tag{font-size:24px;color:#637975}
.steps{display:flex;gap:40px}.step{background:white;border-top:8px solid #167d86;padding:40px;width:530px;height:280px;font-size:32px}
.number{font-size:64px;color:#167d86;margin-bottom:24px}.foot{position:absolute;bottom:80px;font-size:24px}</style></head>
<body><div class="tag">AWF / ENGINEERING EVIDENCE FIXTURE</div><h1>A screenshot needs a traceable source.</h1>
<div class="steps"><div class="step"><div class="number">01</div>Capture the actual HTML</div><div class="step"><div class="number">02</div>Bind the PNG bytes</div><div class="step"><div class="number">03</div>Verify a separate review</div></div>
<p>Changed source or image bytes invalidate the receipt.</p><div class="foot">Browser smoke test. Review signatures use ephemeral test authorities; this is not a production approval.</div></body></html>'''


def run():
    if sys.platform != 'win32':
        raise RuntimeError('Run this browser smoke test on the Windows desktop')
    chrome = Path('C:/Program Files/Google/Chrome/Application/chrome.exe')
    if not chrome.is_file():
        raise FileNotFoundError(chrome)
    fixture = EvidenceFixture(REPORT, html_text=HTML)
    before = file_digest(fixture.html)
    with tempfile.TemporaryDirectory(prefix='awf-design-chrome-') as directory:
        local = Path(directory)
        page, shot = local / 'slide.html', local / 'capture.png'
        shutil.copyfile(fixture.html, page)
        command = [str(chrome), '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
                   '--hide-scrollbars', '--force-device-scale-factor=1', '--window-size=1920,1080',
                   '--user-data-dir=' + str(local / 'profile'), '--screenshot=' + str(shot), page.as_uri()]
        with (REPORT / 'chrome.stdout.txt').open('w') as out, (REPORT / 'chrome.stderr.txt').open('w') as err:
            process = subprocess.run(command, stdout=out, stderr=err, timeout=120, creationflags=subprocess.CREATE_NO_WINDOW, check=False)
        if process.returncode != 0 or not shot.is_file() or file_digest(page) != before or file_digest(fixture.html) != before:
            raise RuntimeError('Browser capture failed or the source changed')
        shutil.copyfile(shot, fixture.png)
    fixture.render['renderer'] = 'Windows Chrome headless, actual isolated-profile --screenshot capture'
    fixture.render['artifacts'][0]['png_sha256'] = file_digest(fixture.png)
    fixture.write()
    result = evaluate_visual_red_blue_adversarial_audit(100, [str(fixture.png)], [], evidence_context=fixture.context, score_payload=fixture.scores)
    if not result['passed']:
        raise AssertionError(result)
    save_json(REPORT / 'receipt.json', {'status': 'PASS', 'actual_browser_capture': True, 'production_review': False,
                                     'png': str(fixture.png), 'html': str(fixture.html), 'acceptance_under_test_authorities': result,
                                     'source_hashes': {str(path.relative_to(ROOT).as_posix()): file_digest(path) for path in [Path(__file__), SOURCE / 'design_tests/evidence_fixtures.py', *[SOURCE / 'scripts' / name for name in ['design_contract.py', 'design_scores.py', 'design_capture_profile.py', 'design_evidence.py', 'design_acceptance.py']]]}})
    print(json.dumps({'status': 'PASS', 'png': str(fixture.png), 'production_review': False}))


if __name__ == '__main__':
    run()
