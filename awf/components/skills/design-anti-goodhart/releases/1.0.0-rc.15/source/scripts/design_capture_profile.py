"""A bounded capture profile: offline self-contained static slides, initial state."""
from html.parser import HTMLParser
from pathlib import Path
from design_contract import file_bytes, require

CAPTURE_PROFILE = 'offline-static-slide-initial-v1'
CSP = "default-src 'none'; img-src data:; style-src 'unsafe-inline'; script-src 'none'; font-src data:; media-src data:; connect-src 'none'; frame-src 'none'; worker-src 'none'; object-src 'none'; base-uri 'none'"
CSP_META = '<meta http-equiv="Content-Security-Policy" content="' + CSP + '">'
LOADING_TAGS = {'script', 'img', 'link', 'source', 'video', 'audio', 'track', 'input', 'image', 'use'}
VOID_TAGS = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}


class UnsupportedCaptureProfile(ValueError):
    """This artifact needs a richer reviewed browser-capture profile."""


class CaptureDocument(HTMLParser):
    def __init__(self):
        super().__init__()
        self.csp_seen = False
        self.slide_count = 0
        self.stack = []
        self.head_seen = False
        self.head_closed = False
        self.body_seen = False

    def handle_starttag(self, tag, attrs):
        require(len(attrs) == len({key for key, _ in attrs}), 'Duplicate HTML attributes are unsupported')
        values = dict(attrs)
        if tag == 'script' or any(key.startswith('on') for key in values):
            raise UnsupportedCaptureProfile('Executable scripts/events need a trusted dynamic-DOM capture profile; static acceptance is unavailable')
        require(tag not in {'base', 'iframe', 'frame', 'object', 'embed'}, 'Unsupported embedded/navigating document')
        if tag == 'html':
            require(not self.stack and not self.head_seen, 'Expected one explicit html root')
        elif tag == 'head':
            require(self.stack == ['html'] and not self.head_seen, 'Expected one explicit head')
            self.head_seen = True
        elif tag == 'body':
            require(self.stack == ['html'] and self.head_closed and self.csp_seen and not self.body_seen, 'Expected one explicit body after the protected head')
            self.body_seen = True
        else:
            require(bool(self.stack) and self.head_seen, 'Implicit document structure is unsupported')
            if not self.head_closed:
                require(self.stack == ['html', 'head'] and tag in {'meta', 'title', 'style', 'link'}, 'Unsupported head nesting or implicit body')
            else:
                require('body' in self.stack, 'Content outside explicit body is unsupported')
        if tag == 'meta':
            directive = (values.get('http-equiv') or '').lower()
            require(directive != 'refresh', 'Automatic document navigation is unsupported')
            if directive == 'content-security-policy':
                require(self.stack == ['html', 'head'], 'CSP must be a direct child of the explicit head')
                require(values.get('content') == CSP, 'The offline capture CSP must match the published profile')
                self.csp_seen = True
        if tag in LOADING_TAGS or tag in {'style', 'body'}:
            require(self.csp_seen, 'Offline CSP must precede renderable/script/style content')
        if tag in LOADING_TAGS:
            for key in ('src', 'href', 'xlink:href', 'poster'):
                value = values.get(key)
                require(not value or value.startswith(('data:', '#')), 'External resources must be embedded before final acceptance')
            require(not values.get('srcset'), 'Embed a single data image instead of external srcset')
        if 'slide' in (values.get('class') or '').split():
            self.slide_count += 1
        if tag not in VOID_TAGS:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        require(bool(self.stack) and self.stack[-1] == tag, 'Malformed HTML nesting is outside the capture profile')
        self.stack.pop()
        if tag == 'head':
            self.head_closed = True

    def handle_data(self, data):
        if data.strip() and not self.head_closed:
            require(bool(self.stack) and self.stack[-1] in {'title', 'style'}, 'Unexpected text before the explicit body')

    def handle_startendtag(self, tag, attrs):
        require(tag in VOID_TAGS, 'Use explicit end tags for non-void elements, including SVG; HTML self-closing semantics are ambiguous')
        self.handle_starttag(tag, attrs)


def capture_frames(html_path):
    document = CaptureDocument()
    document.feed(file_bytes(html_path).decode('utf-8'))
    document.close()
    require(document.csp_seen and document.body_seen and not document.stack, 'Incomplete normalized offline document')
    selector = '.slide' if document.slide_count else 'html'
    return [{'selector': selector, 'index': index, 'state': 'initial'} for index in range(document.slide_count or 1)]


def bound_source_html(context):
    expected = context['expected_artifacts']
    require(isinstance(expected, dict) and bool(expected), 'Runner must identify actual target HTML')
    unique_paths = sorted({str(Path(path).resolve()) for path in expected.values()})
    return '\n'.join(file_bytes(path).decode('utf-8') for path in unique_paths)
