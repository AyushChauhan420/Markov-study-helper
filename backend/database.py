"""
database.py — single place that talks to Supabase.

Uses the SERVICE ROLE key (server-side only, never ship it to the
Streamlit frontend) so the FastAPI backend can read/write freely and
RLS policies only matter for any other client hitting Supabase directly.
"""

import os
from functools import lru_cache

from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")


@lru_cache
def get_supabase() -> Client:
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise RuntimeError(
            "SUPABASE_URL / SUPABASE_SERVICE_KEY are not set. "
            "Copy backend/.env.example to backend/.env and fill them in "
            "(Supabase project settings -> API)."
        )
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
