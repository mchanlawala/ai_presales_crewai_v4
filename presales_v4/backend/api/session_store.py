import json, os, threading
from datetime import datetime
from typing import Dict, Optional

class SessionStore:
    def __init__(self, persist_dir="output/sessions"):
        self._sessions: Dict[str, dict] = {}
        self._lock = threading.RLock()
        self._dir = persist_dir
        os.makedirs(persist_dir, exist_ok=True)

    def create(self, sid: str, query: str) -> dict:
        now = datetime.utcnow().isoformat()
        s = {"session_id": sid, "status": "analyzing", "customer_query": query,
             "industry": None, "requirements": None, "clarifying_questions": None,
             "user_answers": None, "crew_analysis": None, "documents": [],
             "review_comments": None, "progress": 0, "current_step": "Starting",
             "error": None, "created_at": now, "updated_at": now, "zip_path": None}
        with self._lock:
            self._sessions[sid] = s
            self._save(sid)
        return s

    def get(self, sid: str) -> Optional[dict]:
        with self._lock:
            if sid not in self._sessions:
                loaded = self._load(sid)
                if loaded:
                    self._sessions[sid] = loaded
            return self._sessions.get(sid)

    def update(self, sid: str, **kw) -> Optional[dict]:
        with self._lock:
            if sid not in self._sessions:
                return None
            self._sessions[sid].update(kw)
            self._sessions[sid]["updated_at"] = datetime.utcnow().isoformat()
            self._save(sid)
            return self._sessions[sid]

    def list_all(self) -> list:
        with self._lock:
            return list(self._sessions.values())

    def _save(self, sid: str):
        try:
            with open(os.path.join(self._dir, f"{sid}.json"), "w") as f:
                json.dump(self._sessions[sid], f, indent=2, default=str)
        except Exception:
            pass

    def _load(self, sid: str) -> Optional[dict]:
        try:
            p = os.path.join(self._dir, f"{sid}.json")
            if os.path.exists(p):
                with open(p) as f:
                    return json.load(f)
        except Exception:
            pass
        return None

store = SessionStore()
