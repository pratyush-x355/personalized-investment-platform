import logging
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, g
from database import init_db, get_credentials, save_credentials, update_access_token
from kiteconnect import KiteConnect
from core import Kite_Api
import os

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key


def get_kite_api():
    """Get or create Kite API instance for current request"""
    if 'kite_api' not in g:
        credentials = get_credentials()
        access_token = session.get('access_token')
        
        if not credentials or not access_token:
            return None
        
        api_key, _, _ = credentials
        g.kite_api = Kite_Api(api_key=api_key, access_token=access_token)
    
    return g.kite_api


def require_auth():
    """Check if user is authenticated and return kite_api instance"""
    kite_api = get_kite_api()
    if not kite_api:
        return None, jsonify({'error': 'Not authenticated'}), 401
    return kite_api, None, None


@app.route('/')
def index():
    """Main page with setup and login options"""
    credentials = get_credentials()
    return render_template('index.html', has_credentials = credentials is not None)

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    """Setup API credentials"""
    if request.method == 'POST':
        api_key = request.form.get('api_key')
        api_secret = request.form.get('api_secret')
        
        if api_key and api_secret:
            save_credentials(api_key, api_secret)
            flash('API credentials saved successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Please provide both API key and secret', 'error')
    
    return render_template('setup.html')

@app.route('/login')
def login():
    """Generate Kite login URL and redirect user"""
    credentials = get_credentials()
    
    if not credentials:
        flash('Please setup API credentials first', 'error')
        return redirect(url_for('setup'))
    
    api_key, api_secret, _ = credentials
    
    try:
        kite = KiteConnect(api_key=api_key)
        login_url = kite.login_url()
        
        # Store API details in session for callback
        session['api_key'] = api_key
        session['api_secret'] = api_secret
        
        return redirect(login_url)
    
    except Exception as e:
        flash(f'Error generating login URL: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/zerodha/callback/')
def callback():
    """Handle callback from Zerodha after login"""
    request_token = request.args.get('request_token')
    
    if not request_token:
        flash('No request token received', 'error')
        return redirect(url_for('index'))
    
    api_key = session.get('api_key')
    api_secret = session.get('api_secret')
    
    if not api_key or not api_secret:
        flash('Session expired. Please try logging in again.', 'error')
        return redirect(url_for('index'))
    
    try:
        kite = KiteConnect(api_key=api_key)
        data = kite.generate_session(request_token, api_secret=api_secret)
        access_token = data["access_token"]
        
        # Save access token to database
        update_access_token(access_token)
        
        # Set access token for current session
        kite.set_access_token(access_token)
        session['access_token'] = access_token
        
        flash('Successfully logged in to Kite!', 'success')
        return redirect(url_for('home'))
    
    except Exception as e:
        flash(f'Login failed: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/home')
def home():
    """Home page after successful login"""
    access_token = session.get('access_token')
    
    if not access_token:
        flash('Please login first', 'error')
        return redirect(url_for('index'))
    
    return render_template('home.html', access_token=access_token)

@app.route('/profile')
def profile():
    """Get user profile from Kite API"""
    kite_api, error_response, status_code = require_auth()
    if error_response:
        return error_response, status_code
    
    try:
        profile_data = kite_api.get_profile()
        return jsonify(profile_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/holdings')
def holdings():
    """Get holdings from Kite API"""
    kite_api, error_response, status_code = require_auth()
    if error_response:
        return error_response, status_code
    
    try:
        holdings_data = kite_api.get_holdings()
        return jsonify(holdings_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/positions')
def positions():
    """Get positions from Kite API"""
    kite_api, error_response, status_code = require_auth()
    if error_response:
        return error_response, status_code
    
    try:
        positions_data = kite_api.get_positions()
        return jsonify(positions_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/margins')
def margins():
    """Get margins from Kite API"""
    kite_api, error_response, status_code = require_auth()
    if error_response:
        return error_response, status_code
    
    try:
        margins_data = kite_api.get_margins()
        return jsonify(margins_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Create templates directory if it doesn't exist
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    app.run(debug=True, host='127.0.0.1', port=8000)