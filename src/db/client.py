from typing import Optional
from supabase import create_client, Client
from src.config import SUPABASE_URL, SUPABASE_KEY

_supabase_client: Optional[Client] = None


def get_supabase_client() -> Optional[Client]:
    """Returns singleton Supabase client or None if credentials are not configured."""
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    if SUPABASE_URL and SUPABASE_KEY and "your-project" not in SUPABASE_URL:
        try:
            _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception as e:
            print(f"Warning: Failed to initialize Supabase client: {e}")
            _supabase_client = None

    return _supabase_client
