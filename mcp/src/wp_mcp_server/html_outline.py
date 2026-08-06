"""HTML parsing helpers for get_rendered_structure:

- the simplified structural outline (FR-004, data-model.md's OutlineNode)
- the plain-fetch vs. headless-render fallback rule (FR-003, research.md #3)
- the outline's scope: <main> by default, or an explicit selector
  (FR-012, research.md #11)
"""

from __future__ import annotations

import soupsieve
from bs4 import BeautifulSoup, Comment, NavigableString, Tag

_STRIP_TAGS = ("script", "style", "noscript")
_SPA_ROOT_SELECTOR = "#root, #app, #__next, #___gatsby, [data-reactroot]"

_MIN_ELEMENT_DESCENDANTS = 10
_MIN_VISIBLE_TEXT_CHARS = 200

DEFAULT_SCOPE_SELECTOR = "main"


def parse_body(html: str) -> Tag:
    """Parse html and return its <body> (or the document root, for a
    bodyless fragment) with <script>/<style>/<noscript>/comment nodes
    removed."""
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.find_all(_STRIP_TAGS):
        tag.decompose()
    for comment in soup.find_all(string=lambda s: isinstance(s, Comment)):
        comment.extract()

    return soup.body or soup


def needs_render_fallback(body: Tag) -> bool:
    """The exact fallback rule from research.md #3.

    fallback iff (A AND B) OR C, where:
      A: body has fewer than 10 element descendants
      B: body's visible text (whitespace collapsed) is under 200 chars
      C: a #root/#app/#__next/#___gatsby/[data-reactroot] element exists
         with zero direct element children
    """
    element_descendants = body.find_all(True)
    visible_text = body.get_text(strip=True)

    condition_ab = (
        len(element_descendants) < _MIN_ELEMENT_DESCENDANTS
        and len(visible_text) < _MIN_VISIBLE_TEXT_CHARS
    )

    condition_c = any(
        len(root.find_all(True, recursive=False)) == 0
        for root in body.select(_SPA_ROOT_SELECTOR)
    )

    return condition_ab or condition_c


def resolve_outline_root(body: Tag, selector: str | None) -> tuple[Tag, str]:
    """Pick which element the outline is built from (research.md #11).

    - selector given: scope to body.select_one(selector); raises
      ValueError if nothing matches — an explicit request that finds
      nothing is a clear error, not a silent fallback to something else.
    - selector omitted (None): default to the page's <main> landmark when
      present, so repeated site-wide chrome (header/nav/footer/comment
      form) isn't duplicated on every call; fall back to the full body
      when the theme has no semantic <main>.

    Returns (root_element, scope_label) — scope_label is echoed back in
    the tool's response so the caller knows which one actually applied.
    """
    if selector is not None:
        # select_one only searches descendants, but the root passed in
        # here (typically <body> itself) is a valid match target too
        # (e.g. selector="body" to mean "the whole page") — check the
        # root itself before searching its descendants.
        if soupsieve.match(selector, body):
            return body, selector
        root = body.select_one(selector)
        if root is None:
            raise ValueError(f"No element matches selector {selector!r} on this page")
        return root, selector

    main = body.select_one(DEFAULT_SCOPE_SELECTOR)
    if main is not None:
        return main, DEFAULT_SCOPE_SELECTOR
    return body, "body"


def _direct_text(tag: Tag) -> str | None:
    text = "".join(
        child for child in tag.contents if isinstance(child, NavigableString)
    ).strip()
    return text or None


def _build_node(tag: Tag) -> dict:
    node: dict = {"tag": tag.name}

    if tag.get("id"):
        node["id"] = tag["id"]

    classes = tag.get("class")
    if classes:
        node["class"] = classes

    text = _direct_text(tag)
    if text:
        node["text"] = text

    node["children"] = [
        _build_node(child) for child in tag.find_all(True, recursive=False)
    ]
    return node


def build_outline(body: Tag) -> dict:
    """Build the nested OutlineNode structure (data-model.md) from body."""
    return _build_node(body)
