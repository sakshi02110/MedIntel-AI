"""
Supabase Client for MedIntel AI.

Handles Authentication, Session History, and Database interactions.
"""

import os
import json
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

from supabase import create_client, Client
from gotrue.types import User

from src.utils.logger import get_logger

load_dotenv()
logger = get_logger("medintel.supabase_client")


class SupabaseClient:
    """
    Singleton wrapper for Supabase interactions.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupabaseClient, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self._url = os.getenv("SUPABASE_URL", "")
        self._key = os.getenv("SUPABASE_ANON_KEY", "")
        self._client: Optional[Client] = None

        if self._url and self._key:
            try:
                self._client = create_client(self._url, self._key)
                logger.info("Supabase client initialized successfully.")
            except Exception as exc:
                logger.error(f"Failed to initialize Supabase client: {exc}")
        else:
            logger.warning("SUPABASE_URL or SUPABASE_ANON_KEY is missing. Operating in offline/mock mode.")

    @property
    def is_connected(self) -> bool:
        return self._client is not None

    def get_client(self) -> Optional[Client]:
        return self._client

    # ── Auth ──────────────────────────────────────────────────────────────────

    def sign_up(self, email: str, password: str):
        if not self.is_connected:
            raise ConnectionError("Supabase is not connected.")
        return self._client.auth.sign_up({"email": email, "password": password})

    def sign_in(self, email: str, password: str):
        if not self.is_connected:
            raise ConnectionError("Supabase is not connected.")
        return self._client.auth.sign_in_with_password({"email": email, "password": password})

    def sign_out(self):
        if not self.is_connected:
            return
        return self._client.auth.sign_out()

    def get_current_user(self) -> Optional[User]:
        if not self.is_connected:
            return None
        try:
            return self._client.auth.get_user().user
        except Exception:
            return None

    # ── DB: Reports ───────────────────────────────────────────────────────────

    def save_report(self, user_id: str, report_name: str, report_text: str, analysis_json: Dict[str, Any]) -> str:
        """Saves a report and returns its ID."""
        if not self.is_connected:
            return "mock_report_id"
        
        data = {
            "user_id": user_id,
            "report_name": report_name,
            "report_text": report_text,
            "analysis_result": analysis_json
        }
        res = self._client.table("uploaded_reports").insert(data).execute()
        return res.data[0]["report_id"]

    def get_user_reports(self, user_id: str) -> List[Dict[str, Any]]:
        if not self.is_connected:
            return []
        res = self._client.table("uploaded_reports").select("*").eq("user_id", user_id).order("upload_date", desc=True).execute()
        return res.data

    def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        if not self.is_connected:
            return None
        res = self._client.table("uploaded_reports").select("*").eq("report_id", report_id).execute()
        return res.data[0] if res.data else None

    # ── DB: Chat Sessions ─────────────────────────────────────────────────────

    def create_chat_session(self, user_id: str, report_id: str, session_name: str) -> str:
        """Creates a chat session and returns its ID."""
        if not self.is_connected:
            return "mock_session_id"
            
        data = {
            "user_id": user_id,
            "report_id": report_id,
            "session_name": session_name
        }
        res = self._client.table("chat_sessions").insert(data).execute()
        return res.data[0]["session_id"]

    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        if not self.is_connected:
            return []
        res = self._client.table("chat_sessions").select("session_id, session_name, created_at, report_id, uploaded_reports(report_name)").eq("user_id", user_id).order("created_at", desc=True).execute()
        
        # Flatten the nested report_name for ease of use
        sessions = []
        for d in res.data:
            s = dict(d)
            s["report_name"] = d.get("uploaded_reports", {}).get("report_name", "Unknown Report") if d.get("uploaded_reports") else "Unknown Report"
            sessions.append(s)
        return sessions

    def save_chat_message(self, session_id: str, role: str, message: str):
        if not self.is_connected:
            return
        data = {
            "session_id": session_id,
            "role": role,
            "message": message
        }
        self._client.table("chat_messages").insert(data).execute()

    def get_chat_history(self, session_id: str) -> List[Dict[str, Any]]:
        if not self.is_connected:
            return []
        res = self._client.table("chat_messages").select("*").eq("session_id", session_id).order("timestamp", desc=False).execute()
        return res.data
