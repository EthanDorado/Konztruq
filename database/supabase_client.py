from supabase import create_client, Client

from config import SUPABASE_URL, SUPABASE_KEY


def get_supabase_client() -> Client:
    """
    Creates and returns the Supabase client.

    The Supabase client is the object our Python application
    will use to communicate with the Supabase database.
    """
    return create_client(SUPABASE_URL, SUPABASE_KEY)