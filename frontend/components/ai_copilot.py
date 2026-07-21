"""frontend/components/ai_copilot.py — HirePilot AI Copilot Component

Re-exports the AI Copilot page renderer from views. The full chat logic now lives in
frontend/views/ai_copilot.py and frontend/services/copilot_service.py.
"""

from frontend.views.ai_copilot import render_ai_copilot

__all__ = ["render_ai_copilot"]
