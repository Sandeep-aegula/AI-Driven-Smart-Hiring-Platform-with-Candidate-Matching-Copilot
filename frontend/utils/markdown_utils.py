"""utils/markdown_utils.py - Markdown utility functions.

Utility functions for markdown rendering.
"""

import re


def render_markdown(text: str) -> str:
    """Render markdown text with basic formatting."""
    # Escape HTML
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # Bold
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)

    # Italic
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)

    # Code blocks
    text = re.sub(r"```(.*?)```", r"<pre><code>\1</code></pre>", text, flags=re.DOTALL)

    # Inline code
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)

    # Line breaks
    text = text.replace("\n", "<br>")

    return text
