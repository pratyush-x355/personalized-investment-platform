# database/auth_db.py
import sqlite3
import os

# Credentials database path
CREDENTIALS_DB = 'data/credentials.db'

def init_credentials_db():
    """Initialize credentials database"""
    os.makedirs('data', exist_ok=True)
    conn = sqlite3.connect(CREDENTIALS_DB)
    cursor = conn.cursor()
    
    # API Credentials
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_credentials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key TEXT NOT NULL,
            api_secret TEXT NOT NULL,
            access_token TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        )
    ''')
    
    # User settings (sensitive configurations)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_key TEXT NOT NULL UNIQUE,
            setting_value TEXT,
            is_encrypted BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Login sessions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_token TEXT UNIQUE,
            user_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        )
    ''')
    
    conn.commit()
    conn.close()

def get_credentials():
    """Get the latest API credentials"""
    conn = sqlite3.connect(CREDENTIALS_DB)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT api_key, api_secret, access_token 
        FROM api_credentials 
        WHERE is_active = TRUE 
        ORDER BY id DESC LIMIT 1
    ''')
    result = cursor.fetchone()
    conn.close()
    return result

def save_credentials(api_key, api_secret):
    """Save new API credentials"""
    conn = sqlite3.connect(CREDENTIALS_DB)
    cursor = conn.cursor()
    
    # Deactivate old credentials
    cursor.execute('UPDATE api_credentials SET is_active = FALSE')
    
    # Insert new credentials
    cursor.execute('''
        INSERT INTO api_credentials (api_key, api_secret, is_active)
        VALUES (?, ?, TRUE)
    ''', (api_key, api_secret))
    
    conn.commit()
    conn.close()

def update_access_token(access_token):
    """Update access token"""
    conn = sqlite3.connect(CREDENTIALS_DB)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE api_credentials 
        SET access_token = ? 
        WHERE is_active = TRUE
    ''', (access_token,))
    conn.commit()
    conn.close()

def save_user_setting(key, value, is_encrypted=False):
    """Save user setting"""
    conn = sqlite3.connect(CREDENTIALS_DB)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO user_settings (setting_key, setting_value, is_encrypted, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
    ''', (key, value, is_encrypted))
    conn.commit()
    conn.close()

def get_user_setting(key):
    """Get user setting"""
    conn = sqlite3.connect(CREDENTIALS_DB)
    cursor = conn.cursor()
    cursor.execute('SELECT setting_value FROM user_settings WHERE setting_key = ?', (key,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None
