# database/__init__.py
from .auth_db import init_db, get_credentials, save_credentials, update_access_token

# Only these functions are easily accessible
# Internal functions stay hidden