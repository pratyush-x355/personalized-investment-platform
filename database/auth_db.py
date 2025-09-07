import sqlite3
import os
# Credentials database path
CREDENTIALS_DB = 'data/credentials.db'

# Database setup
def init_db():
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(CREDENTIALS_DB), exist_ok=True)
    conn = sqlite3.connect(CREDENTIALS_DB)
    cursor = conn.cursor()
    # Create table for storing API credentials
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_credentials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key TEXT NOT NULL,
            api_secret TEXT NOT NULL,
            access_token TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def get_credentials():
    """Get the latest API credentials from database"""
    conn = sqlite3.connect(CREDENTIALS_DB)
    cursor = conn.cursor()
    cursor.execute('SELECT api_key, api_secret, access_token FROM api_credentials ORDER BY id DESC LIMIT 1')
    result = cursor.fetchone()
    conn.close()
    return result

def save_credentials(api_key, api_secret):
    """Save API credentials to database"""
    conn = sqlite3.connect(CREDENTIALS_DB)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO api_credentials (api_key, api_secret) VALUES (?, ?)', (api_key, api_secret))
    conn.commit()
    conn.close()

def update_access_token(access_token):
    """Update access token in database"""
    conn = sqlite3.connect(CREDENTIALS_DB)
    cursor = conn.cursor()
    cursor.execute('UPDATE api_credentials SET access_token = ? WHERE id = (SELECT MAX(id) FROM api_credentials)', (access_token,))
    conn.commit()
    conn.close()