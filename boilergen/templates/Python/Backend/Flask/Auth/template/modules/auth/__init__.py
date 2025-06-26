import os

from dotenv import load_dotenv
from supabase import create_client, Client
from supabase.lib.client_options import SyncClientOptions

load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_ANON_KEY")
client: Client = create_client(url, key, options=SyncClientOptions(
    auto_refresh_token=False))  # https://github.com/supabase/supabase/issues/14234