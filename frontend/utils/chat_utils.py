"""utils/chat_utils.py - Chat utility functions.

Utility functions for the AI Assistant chat.
"""

import time
import uuid
from typing import Optional


def generate_message_id() -> str:
    """Generate a unique message ID."""
    return f"msg_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"


def get_timestamp() -> str:
    """Get current timestamp as string."""
    return time.strftime("%I:%M %p")


def render_markdown(text: str) -> str:
    """Render markdown text with basic formatting."""
    import re
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


def auto_scroll_to_bottom() -> None:
    """Auto-scroll chat to bottom (handled by Streamlit)."""
    pass
