# src/ui/__init__.py
from .auth_page import render_auth_page
from .dashboard import render_dashboard
from .upload_page import render_upload_page
from .chat_page import render_chat_page
from .trends_page import render_trends_page
from .doctor_page import render_doctor_page
from .settings_page import render_settings_page

__all__ = [
    "render_auth_page",
    "render_dashboard",
    "render_upload_page",
    "render_chat_page",
    "render_trends_page",
    "render_doctor_page",
    "render_settings_page"
]
