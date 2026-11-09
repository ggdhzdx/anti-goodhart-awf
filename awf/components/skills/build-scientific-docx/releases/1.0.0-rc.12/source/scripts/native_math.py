#!/usr/bin/env python3
"""Insert strict, editable OMML equations into DOCX files.

This module implements a deliberately bounded LaTeX subset. Unknown commands
raise LatexSyntaxError; there is no image fallback.
"""

from __future__ import annotations

import argparse
import copy
import os
from pathlib import Path
import re
import tempfile
import zipfile

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt


class LatexSyntaxError(ValueError):
    """Raised when the strict LaTeX subset cannot represent an expression."""


SYMBOLS = {
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ",
    "epsilon": "ε", "varepsilon": "ϵ", "zeta": "ζ", "eta": "η",
    "theta": "θ", "vartheta": "ϑ", "iota": "ι", "kappa": "κ",
    "lambda": "λ", "mu": "μ", "nu": "ν", "xi": "ξ", "pi": "π",
    "rho": "ρ", "sigma": "σ", "tau": "τ", "upsilon": "υ",
    "phi": "φ", "varphi": "ϕ", "chi": "χ", "psi": "ψ", "omega": "ω",
    "Gamma": "Γ", "Delta": "Δ", "Theta": "Θ", "Lambda": "Λ",
    "Xi": "Ξ", "Pi": "Π", "Sigma": "Σ", "Phi": "Φ", "Psi": "Ψ",
    "Omega": "Ω", "cdot": "⋅", "times": "×", "pm": "±", "mp": "∓",
    "le": "≤", "leq": "≤", "ge": "≥", "geq": "≥", "neq": "≠",
    "ne": "≠", "approx": "≈", "sim": "∼", "propto": "∝", "equiv": "≡",
    "gg": "≫", "ll": "≪",
    "in": "∈", "notin": "∉", "subset": "⊂", "supset": "⊃",
    "partial": "∂", "nabla": "∇", "infty": "∞", "hbar": "ℏ",
    "ddagger": "‡", "dagger": "†", "permil": "‰", "models": "⊨",
    "perp": "⊥", "parallel": "∥", "forall": "∀", "exists": "∃",
    "AA": "Å", "circ": "∘", "degree": "°", "bullet": "•",
    "oplus": "⊕", "ominus": "⊖",
    "dots": "…", "ldots": "…", "cdots": "⋯",
    "sum": "∑", "prod": "∏", "int": "∫", "iint": "∬", "iiint": "∭", "oint": "∮", "mid": "|",
    "to": "→", "gets": "←", "rightarrow": "→", "leftarrow": "←",
    "leftrightarrow": "↔", "Rightarrow": "⇒", "Leftarrow": "⇐",
    "rightleftharpoons": "⇌", "leftrightharpoons": "⇌",
    "langle": "⟨", "rangle": "⟩", "lbrace": "{", "rbrace": "}",
    "vert": "|", "Vert": "‖", "lvert": "|", "rvert": "|",
    "lVert": "‖", "rVert": "‖",
    "quad": " ", "qquad": "  ", ",": " ",
    ";": " ", ":": " ", "!": "", "_": "_", "%": "%", "#": "#",
    "&": "&", "{": "{", "}": "}",
}

ACCENT_CHARS = {
    "hat": "^",
    "tilde": "~",
    "vec": "→",
    "dot": "˙",
    "ddot": "¨",
}

ROMAN_OPERATORS = {
    "sin", "cos", "tan", "exp", "log", "ln", "min", "max", "lim",
    "arccos", "arcsin", "arctan", "det",
}

GREEK_AND_PREFIX_COMMANDS = {
    "alpha", "beta", "gamma", "delta", "epsilon", "varepsilon", "zeta", "eta",
    "theta", "vartheta", "iota", "kappa", "lambda", "mu", "nu", "xi", "pi",
    "rho", "sigma", "tau", "upsilon", "phi", "varphi", "chi", "psi", "omega",
    "Gamma", "Delta", "Theta", "Lambda", "Xi", "Pi", "Sigma", "Phi", "Psi", "Omega",
    "partial", "nabla", "hbar", "langle", "lvert", "lVert", "infty", "ddagger", "dagger",
}

PLACEHOLDER = re.compile(r"^\s*\{\{OMML:\s*(.*)\s*\}\}\s*$")
INLINE_PLACEHOLDER = re.compile(r"\{\{OMML_INLINE:\s*(.*?)\s*\}\}")


def _find_inline_placeholders(text: str) -> list[tuple[int, int, str]]:
    """Find {{OMML_INLINE: ...}} spans while respecting balanced {...} inside the formula."""
    spans: list[tuple[int, int, str]] = []
    marker = "{{OMML_INLINE:"
    pos = 0
    n = len(text)
    while True:
        start = text.find(marker, pos)
        if start == -1:
            break
        i = start + len(marker)
        brace_depth = 0
        closed_at = -1
        while i < n:
            ch = text[i]
            if ch == "\\" and i + 1 < n:
                i += 2
                continue
            if ch == "{":
                brace_depth += 1
            elif ch == "}":
                if brace_depth > 0:
                    brace_depth -= 1
                elif text.startswith("}}", i):
                    closed_at = i
                    break
            i += 1
        if closed_at != -1:
            formula = text[start + len(marker):closed_at].strip()
            end_pos = closed_at + 2
            while end_pos < n and text[end_pos] == '}':
                end_pos += 1
            spans.append((start, end_pos, formula))
            pos = end_pos
        else:
            m = INLINE_PLACEHOLDER.search(text, start)
            if not m:
                break
            spans.append((m.start(), m.end(), m.group(1).strip()))
            pos = m.end()
    return spans


def _has_content(node) -> bool:
    kind = node[0]
    if kind == "text":
        return bool(node[1].strip())
    if kind == "seq":
        return any(_has_content(child) for child in node[1])
    return True


def _node_to_text(node) -> str:
    if isinstance(node, str):
        return node
    kind = node[0]
    if kind == "text":
        return node[1]
    if kind == "seq":
        return "".join(_node_to_text(child) for child in node[1])
    if kind in {"roman", "bold"}:
        return _node_to_text(node[1])
    raise LatexSyntaxError(f"invalid operator name: {kind}")


class LatexParser:
    def __init__(self, source: str):
        source = source.strip()
        if source.startswith("$$") and source.endswith("$$") and len(source) >= 4:
            source = source[2:-2].strip()
        elif source.startswith("$") and source.endswith("$") and len(source) >= 2:
            source = source[1:-1].strip()
        elif source.startswith(r"\[") and source.endswith(r"\]"):
            source = source[2:-2].strip()
        if not source:
            raise LatexSyntaxError("empty equation")
        self.source = source
        self.pos = 0

    def parse(self):
        node = self.parse_sequence()
        if self.pos != len(self.source):
            raise LatexSyntaxError(f"unparsed text at position {self.pos}")
        return node

    def parse_sequence(self, stop: str | None = None):
        nodes = []
        while self.pos < len(self.source):
            if stop == r"\right" and self.source.startswith(r"\right", self.pos):
                after = self.pos + 6
                if after == len(self.source) or not self.source[after].isalpha():
                    return ("seq", nodes)
            char = self.source[self.pos]
            if char == "}":
                if stop == "}":
                    self.pos += 1
                    return ("seq", nodes)
                raise LatexSyntaxError(f"unmatched closing brace at position {self.pos}")
            if char == ")":
                if stop == ")":
                    self.pos += 1
                    return ("seq", nodes)
                raise LatexSyntaxError(f"unmatched closing parenthesis at position {self.pos}")
            if char == "]":
                if stop == "]":
                    self.pos += 1
                    return ("seq", nodes)
                raise LatexSyntaxError(f"unmatched closing bracket at position {self.pos}")
            if char == "|":
                if stop == "|":
                    self.pos += 1
                    return ("seq", nodes)
            if char in "_^":
                raise LatexSyntaxError(f"{char} has no base at position {self.pos}")
            atom = self.parse_atom()
            sub = sup = None
            while True:
                save_pos = self.pos
                while self.pos < len(self.source) and self.source[self.pos].isspace():
                    self.pos += 1
                if self.pos < len(self.source) and self.source[self.pos] in "_^":
                    marker = self.source[self.pos]
                    self.pos += 1
                    value = self.parse_group_or_atom()
                    if marker == "_":
                        if sub is not None:
                            raise LatexSyntaxError("duplicate subscript")
                        sub = value
                    else:
                        if sup is not None:
                            raise LatexSyntaxError("duplicate superscript")
                        sup = value
                else:
                    self.pos = save_pos
                    break
            if atom[0] == "nary":
                chr_val = atom[1]
                operator_sub = sub
                operator_sup = sup
                body = self.parse_arg_or_body()
                atom = ("nary", chr_val, operator_sub, operator_sup, body)
            else:
                if sub is not None and sup is not None:
                    atom = ("subsup", atom, sub, sup)
                elif sub is not None:
                    atom = ("sub", atom, sub)
                elif sup is not None:
                    atom = ("sup", atom, sup)
            nodes.append(atom)
        if stop == r"\right":
            raise LatexSyntaxError("unclosed \\left")
        if stop == ")":
            raise LatexSyntaxError("unclosed parenthesis")
        if stop == "]":
            raise LatexSyntaxError("unclosed bracket")
        if stop == "|":
            raise LatexSyntaxError("unclosed absolute value")
        if stop is not None:
            raise LatexSyntaxError("unclosed group")
        return ("seq", nodes)

    def parse_group_or_atom(self):
        while self.pos < len(self.source) and self.source[self.pos].isspace():
            self.pos += 1
        if self.pos >= len(self.source):
            raise LatexSyntaxError("missing argument")
        if self.source[self.pos] == "{":
            self.pos += 1
            return self.parse_sequence("}")
        return self.parse_atom(single_literal=True)

    def parse_atom(self, single_literal: bool = False):
        if self.pos >= len(self.source):
            raise LatexSyntaxError("unexpected end of expression")
        char = self.source[self.pos]
        if char == "{":
            self.pos += 1
            return self.parse_sequence("}")
        if char == "(":
            self.pos += 1
            inner = self.parse_sequence(")")
            return ("d", "(", ")", inner)
        if char == "[":
            self.pos += 1
            inner = self.parse_sequence("]")
            return ("d", "[", "]", inner)
        if char == "|":
            self.pos += 1
            inner = self.parse_sequence("|")
            if not _has_content(inner):
                raise LatexSyntaxError("empty absolute value")
            return ("d", "|", "|", inner)
        if char == "\\":
            return self.parse_command()
        if char == "}":
            raise LatexSyntaxError(f"unexpected closing brace at position {self.pos}")
        if char == ")":
            raise LatexSyntaxError(f"unexpected closing parenthesis at position {self.pos}")
        if char == "]":
            raise LatexSyntaxError(f"unexpected closing bracket at position {self.pos}")
        start = self.pos
        if single_literal:
            self.pos += 1
        else:
            while self.pos < len(self.source) and self.source[self.pos] not in "\\{}_^()[]|":
                self.pos += 1
        return ("text", self.source[start:self.pos], False)

    def parse_arg_or_body(self):
        while self.pos < len(self.source) and self.source[self.pos].isspace():
            self.pos += 1
        if self.pos >= len(self.source):
            raise LatexSyntaxError("missing argument")
        if self.source.startswith(r"\right", self.pos):
            after = self.pos + 6
            if after == len(self.source) or not self.source[after].isalpha():
                raise LatexSyntaxError("missing argument")
        char = self.source[self.pos]
        if char == "}":
            raise LatexSyntaxError(f"unexpected closing brace at position {self.pos}")
        if char == ")":
            raise LatexSyntaxError(f"unexpected closing parenthesis at position {self.pos}")
        if char == "]":
            raise LatexSyntaxError(f"unexpected closing bracket at position {self.pos}")
        if char in "_^":
            raise LatexSyntaxError(f"{char} has no base at position {self.pos}")
        if char == "{":
            self.pos += 1
            arg = self.parse_sequence("}")
            if not arg[1]:
                raise LatexSyntaxError("missing argument")
        else:
            arg = self.parse_atom(single_literal=True)
        sub = sup = None
        while True:
            save_pos = self.pos
            while self.pos < len(self.source) and self.source[self.pos].isspace():
                self.pos += 1
            if self.pos < len(self.source) and self.source[self.pos] in "_^":
                marker = self.source[self.pos]
                self.pos += 1
                value = self.parse_group_or_atom()
                if marker == "_":
                    if sub is not None:
                        raise LatexSyntaxError("duplicate subscript")
                    sub = value
                else:
                    if sup is not None:
                        raise LatexSyntaxError("duplicate superscript")
                    sup = value
            else:
                self.pos = save_pos
                break
        if sub is not None and sup is not None:
            arg = ("subsup", arg, sub, sup)
        elif sub is not None:
            arg = ("sub", arg, sub)
        elif sup is not None:
            arg = ("sup", arg, sup)
        return arg

    def parse_operator_name(self) -> str:
        while self.pos < len(self.source) and self.source[self.pos].isspace():
            self.pos += 1
        if self.pos >= len(self.source):
            raise LatexSyntaxError("missing operator name")
        if self.source[self.pos] == "{":
            self.pos += 1
            node = self.parse_sequence("}")
            if not node[1]:
                raise LatexSyntaxError("missing operator name")
        else:
            node = self.parse_atom(single_literal=True)
        name = _node_to_text(node).strip()
        if not name:
            raise LatexSyntaxError("missing operator name")
        return name

    def parse_nary(self, command: str):
        return ("nary", SYMBOLS[command])

    def parse_command(self):
        command_start = self.pos
        self.pos += 1
        if self.pos >= len(self.source):
            raise LatexSyntaxError("trailing backslash")
        start = self.pos
        if self.source[self.pos].isalpha():
            while self.pos < len(self.source) and self.source[self.pos].isalpha():
                self.pos += 1
        else:
            self.pos += 1
        command = self.source[start:self.pos]
        if command in {"mathrm", "text"}:
            return ("roman", self.parse_group_or_atom())
        if command == "operatorname":
            op_name = self.parse_operator_name()
            arg = self.parse_arg_or_body()
            return ("func", op_name, arg)
        if command == "mathbf":
            return ("bold", self.parse_group_or_atom())
        if command in {"bar", "overline"}:
            return ("bar", self.parse_group_or_atom())
        if command in ACCENT_CHARS:
            return ("acc", ACCENT_CHARS[command], self.parse_group_or_atom())
        if command == "frac":
            return ("frac", self.parse_group_or_atom(), self.parse_group_or_atom())
        if command == "sqrt":
            if self.pos < len(self.source) and self.source[self.pos] == "[":
                raise LatexSyntaxError("optional root degrees are not supported")
            return ("sqrt", self.parse_group_or_atom())
        if command == "left":
            beg_chr = self.parse_delimiter()
            inner = self.parse_sequence(stop=r"\right")
            if not self.source.startswith(r"\right", self.pos):
                raise LatexSyntaxError("unclosed \\left")
            self.pos += 6
            end_chr = self.parse_delimiter()
            return ("d", beg_chr, end_chr, inner)
        if command == "right":
            raise LatexSyntaxError(f"unmatched \\right at position {command_start}")
        if command == "middle":
            return ("text", self.parse_delimiter(), False)
        if command in {"sum", "prod", "int", "iint", "iiint", "oint"}:
            return self.parse_nary(command)
        if command in ROMAN_OPERATORS:
            arg = self.parse_arg_or_body()
            return ("func", command, arg)
        if command in SYMBOLS:
            if command in GREEK_AND_PREFIX_COMMANDS:
                while self.pos < len(self.source) and self.source[self.pos] == " ":
                    self.pos += 1
            return ("text", SYMBOLS[command], False)
        raise LatexSyntaxError(
            f"unsupported command \\{command} at position {command_start}"
        )

    def parse_delimiter(self) -> str:
        while self.pos < len(self.source) and self.source[self.pos].isspace():
            self.pos += 1
        if self.pos >= len(self.source):
            raise LatexSyntaxError("missing delimiter after \\left or \\right")
        char = self.source[self.pos]
        if char != "\\":
            self.pos += 1
            if char in "()[]|":
                return char
            if char == ".":
                return ""
            raise LatexSyntaxError(f"unsupported delimiter {char}")
        self.pos += 1
        if self.pos >= len(self.source):
            raise LatexSyntaxError("missing delimiter after \\")
        if self.source[self.pos] in "{}":
            delim = self.source[self.pos]
            self.pos += 1
            return delim
        if self.source[self.pos] == "|":
            self.pos += 1
            return "‖"
        start = self.pos
        while self.pos < len(self.source) and self.source[self.pos].isalpha():
            self.pos += 1
        command = self.source[start:self.pos]
        if command not in {"langle", "rangle", "lbrace", "rbrace", "vert", "Vert", "lvert", "rvert", "lVert", "rVert"}:
            raise LatexSyntaxError(f"unsupported delimiter \\{command}")
        return SYMBOLS[command]


def _m(tag: str):
    return OxmlElement(f"m:{tag}")


def _m_run(text: str, style: str | None = None):
    run = _m("r")
    if style:
        run_properties = _m("rPr")
        style_node = _m("sty")
        style_node.set(qn("m:val"), style)
        run_properties.append(style_node)
        run.append(run_properties)
    text_node = _m("t")
    text_node.text = text
    run.append(text_node)
    return run


def _append_omml(parent, node, style: str | None = None) -> None:
    kind = node[0]
    if kind == "seq":
        for child in node[1]:
            _append_omml(parent, child, style)
    elif kind == "text":
        if node[1]:
            parent.append(_m_run(node[1], "p" if node[2] else style))
    elif kind == "roman":
        _append_omml(parent, node[1], "p")
    elif kind == "bold":
        _append_omml(parent, node[1], "b")
    elif kind == "bar":
        bar = _m("bar")
        properties = _m("barPr")
        position = _m("pos")
        position.set(qn("m:val"), "top")
        properties.append(position)
        bar.append(properties)
        body = _m("e")
        _append_omml(body, node[1], style)
        bar.append(body)
        parent.append(bar)
    elif kind in {"hat", "acc"}:
        chr_val = "^" if kind == "hat" else node[1]
        base_node = node[1] if kind == "hat" else node[2]
        acc = _m("acc")
        properties = _m("accPr")
        chr_elem = _m("chr")
        chr_elem.set(qn("m:val"), chr_val)
        properties.append(chr_elem)
        acc.append(properties)
        body = _m("e")
        _append_omml(body, base_node, style)
        acc.append(body)
        parent.append(acc)
    elif kind in {"sub", "sup", "subsup"}:
        tag = {"sub": "sSub", "sup": "sSup", "subsup": "sSubSup"}[kind]
        script = _m(tag)
        base = _m("e")
        _append_omml(base, node[1], style)
        script.append(base)
        if kind in {"sub", "subsup"}:
            subscript = _m("sub")
            _append_omml(subscript, node[2], style)
            script.append(subscript)
        if kind == "sup":
            superscript_node = node[2]
        elif kind == "subsup":
            superscript_node = node[3]
        else:
            superscript_node = None
        if superscript_node is not None:
            superscript = _m("sup")
            _append_omml(superscript, superscript_node, style)
            script.append(superscript)
        parent.append(script)
    elif kind == "frac":
        fraction = _m("f")
        numerator = _m("num")
        denominator = _m("den")
        _append_omml(numerator, node[1], style)
        _append_omml(denominator, node[2], style)
        fraction.extend([numerator, denominator])
        parent.append(fraction)
    elif kind == "sqrt":
        radical = _m("rad")
        properties = _m("radPr")
        degree_hide = _m("degHide")
        degree_hide.set(qn("m:val"), "1")
        properties.append(degree_hide)
        radical.extend([properties, _m("deg")])
        body = _m("e")
        _append_omml(body, node[1], style)
        radical.append(body)
        parent.append(radical)
    elif kind == "nary":
        chr_val = node[1]
        sub_node = node[2]
        sup_node = node[3]
        body_node = node[4] if len(node) > 4 else None
        nary = _m("nary")
        properties = _m("naryPr")
        chr_elem = _m("chr")
        chr_elem.set(qn("m:val"), chr_val)
        properties.append(chr_elem)
        if sub_node is None:
            sub_hide = _m("subHide")
            sub_hide.set(qn("m:val"), "1")
            properties.append(sub_hide)
        if sup_node is None:
            sup_hide = _m("supHide")
            sup_hide.set(qn("m:val"), "1")
            properties.append(sup_hide)
        nary.append(properties)
        sub_elem = _m("sub")
        if sub_node is not None:
            _append_omml(sub_elem, sub_node, style)
        sup_elem = _m("sup")
        if sup_node is not None:
            _append_omml(sup_elem, sup_node, style)
        body_elem = _m("e")
        if body_node is not None:
            _append_omml(body_elem, body_node, style)
        nary.extend([sub_elem, sup_elem, body_elem])
        parent.append(nary)
    elif kind == "d":
        d = _m("d")
        properties = _m("dPr")
        beg_char = _m("begChr")
        beg_char.set(qn("m:val"), node[1])
        end_char = _m("endChr")
        end_char.set(qn("m:val"), node[2])
        properties.extend([beg_char, end_char])
        d.append(properties)
        body = _m("e")
        _append_omml(body, node[3], style)
        d.append(body)
        parent.append(d)
    elif kind == "func":
        func = _m("func")
        fname = _m("fName")
        _append_omml(fname, ("text", node[1], True))
        body = _m("e")
        _append_omml(body, node[2], style)
        func.extend([fname, body])
        parent.append(func)
    else:
        raise LatexSyntaxError(f"unsupported parsed node: {kind}")


def inline_equation_element(parsed):
    math = _m("oMath")
    _append_omml(math, parsed)
    return math


def equation_element(parsed):
    math_paragraph = _m("oMathPara")
    math_paragraph.append(inline_equation_element(parsed))
    return math_paragraph


def _clear_paragraph(paragraph) -> None:
    for child in list(paragraph._p):
        if child.tag != qn("w:pPr"):
            paragraph._p.remove(child)


def _strip_indent_and_exact_line_spacing(paragraph) -> None:
    """Remove first-line indent and exact line spacing so display equations are never clipped."""
    pPr = paragraph._p.find(qn("w:pPr"))
    if pPr is not None:
        ind = pPr.find(qn("w:ind"))
        if ind is not None:
            pPr.remove(ind)
        sp = pPr.find(qn("w:spacing"))
        if sp is not None:
            if sp.get(qn("w:lineRule")) == "exact":
                sp.attrib.pop(qn("w:line"), None)
                sp.attrib.pop(qn("w:lineRule"), None)


def replace_paragraph_with_equation(paragraph, parsed) -> None:
    _clear_paragraph(paragraph)
    _strip_indent_and_exact_line_spacing(paragraph)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(4)
    paragraph.paragraph_format.space_after = Pt(4)
    paragraph._p.append(equation_element(parsed))


def _replace_inline_in_paragraph(paragraph, parsed_segments: list[tuple[str, object | None]]) -> None:
    first_rPr = None
    for r in paragraph._p.findall(qn("w:r")):
        rPr = r.find(qn("w:rPr"))
        if rPr is not None:
            first_rPr = copy.deepcopy(rPr)
            break
    _clear_paragraph(paragraph)
    for text_part, parsed_math in parsed_segments:
        if text_part:
            r = OxmlElement("w:r")
            if first_rPr is not None:
                r.append(copy.deepcopy(first_rPr))
            t = OxmlElement("w:t")
            if text_part.startswith(" ") or text_part.endswith(" "):
                t.set(qn("xml:space"), "preserve")
            t.text = text_part
            r.append(t)
            paragraph._p.append(r)
        if parsed_math is not None:
            omath = inline_equation_element(parsed_math)
            if first_rPr is not None:
                for mr in omath.findall(f".//{qn('m:r')}"):
                    w_rPr = OxmlElement("w:rPr")
                    for tag_name in ("w:sz", "w:szCs", "w:b", "w:bCs", "w:color"):
                        el = first_rPr.find(qn(tag_name))
                        if el is not None:
                            w_rPr.append(copy.deepcopy(el))
                    if len(w_rPr) > 0:
                        mr.insert(0, w_rPr)
            paragraph._p.append(omath)


def iter_paragraphs(document):
    yield from document.paragraphs
    seen_tcs = []

    def walk_tables(tables):
        for table in tables:
            for row in table.rows:
                for cell in row.cells:
                    if any(cell._tc is tc for tc in seen_tcs):
                        continue
                    seen_tcs.append(cell._tc)
                    yield from cell.paragraphs
                    yield from walk_tables(cell.tables)

    yield from walk_tables(document.tables)


def render_placeholders(document) -> int:
    display_replacements = []
    inline_replacements = []
    total_equations = 0
    for paragraph in iter_paragraphs(document):
        text = paragraph.text
        match = PLACEHOLDER.fullmatch(text)
        if match:
            formula = match.group(1).strip()
            display_replacements.append((paragraph, LatexParser(formula).parse()))
            total_equations += 1
            continue
        if "{{OMML_INLINE:" in text:
            spans = _find_inline_placeholders(text)
            if spans:
                segments: list[tuple[str, object | None]] = []
                last_end = 0
                for span_start, span_end, formula in spans:
                    prefix = text[last_end:span_start]
                    parsed = LatexParser(formula).parse()
                    segments.append((prefix, parsed))
                    total_equations += 1
                    last_end = span_end
                tail = text[last_end:]
                if tail:
                    segments.append((tail, None))
                inline_replacements.append((paragraph, segments))
    for paragraph, parsed in display_replacements:
        replace_paragraph_with_equation(paragraph, parsed)
    for paragraph, segments in inline_replacements:
        _replace_inline_in_paragraph(paragraph, segments)
    return total_equations


def _save_new(document, output: Path) -> None:
    output = output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output}")
    handle = tempfile.NamedTemporaryFile(
        prefix=f".{output.stem}.", suffix=".tmp.docx", dir=output.parent, delete=False
    )
    temporary = Path(handle.name)
    handle.close()
    try:
        document.save(temporary)
        with zipfile.ZipFile(temporary) as archive:
            bad_member = archive.testzip()
            if bad_member:
                raise ValueError(f"corrupt DOCX member: {bad_member}")
        os.link(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)


def render_file(input_path: Path, output_path: Path) -> int:
    input_path = input_path.expanduser().resolve()
    output_path = output_path.expanduser().resolve()
    if input_path == output_path:
        raise ValueError("input and output paths must differ")
    document = Document(input_path)
    count = render_placeholders(document)
    if count == 0:
        raise ValueError("no {{OMML: ...}} or {{OMML_INLINE: ...}} placeholders found")
    _save_new(document, output_path)
    return count


def create_file(output_path: Path, formulas: list[str]) -> int:
    parsed = [LatexParser(formula).parse() for formula in formulas]
    document = Document()
    document.add_heading("Native Word equation fixture", level=1)
    document.add_paragraph("The equations below are editable OMML objects.")
    for node in parsed:
        paragraph = document.add_paragraph()
        replace_paragraph_with_equation(paragraph, node)
    _save_new(document, output_path)
    return len(parsed)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    render = subparsers.add_parser("render", help="replace exact OMML placeholders")
    render.add_argument("input", type=Path)
    render.add_argument("output", type=Path)
    create = subparsers.add_parser("create", help="create a native-equation fixture")
    create.add_argument("output", type=Path)
    create.add_argument("--formula", action="append", required=True)
    subparsers.add_parser("supported", help="list supported commands")
    return parser


def main() -> int:
    arguments = build_parser().parse_args()
    if arguments.command == "supported":
        print("symbols:", " ".join(f"\\{name}" for name in sorted(SYMBOLS)))
        print("operators:", " ".join(f"\\{name}" for name in sorted(ROMAN_OPERATORS)))
        print("accents:", " ".join(f"\\{name}" for name in sorted(ACCENT_CHARS)))
        print(r"structures: \frac \sqrt \bar \overline \hat \tilde \vec \dot \ddot \mathrm \text \operatorname \mathbf")
        return 0
    if arguments.command == "render":
        count = render_file(arguments.input, arguments.output)
    else:
        count = create_file(arguments.output, arguments.formula)
    print(f"created {arguments.output} with {count} native OMML equation(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
