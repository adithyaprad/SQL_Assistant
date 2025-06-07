import os
import json
from flask import Flask, redirect, url_for, session, request, render_template
from markupsafe import Markup
from authlib.integrations.flask_client import OAuth
from functools import wraps
import subprocess
from datetime import timedelta
from dotenv import load_dotenv
import datetime as import_datetime

load_dotenv()

from multi_tool_agent.agent import call_agent

app = Flask(__name__, template_folder='templates')
app.secret_key = os.getenv('SECRET_KEY', os.urandom(24))
app.config['SESSION_COOKIE_NAME'] = 'google-login-session'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Make session permanent by default
@app.before_request
def make_session_permanent():
    session.permanent = True

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id="13184616137-03u4hfa3i9cca2jnk6uh2lehhk1jkflt.apps.googleusercontent.com",
    client_secret="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",
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'user' in session:
        user = session['user']
        return render_template('index.html', user=user)
    return render_template('index.html')

@app.route('/login')
def login():
    # Clear any existing session first
    session.clear()
    redirect_uri = url_for('callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/callback')
def callback():
    try:
        token = google.authorize_access_token()
        userinfo_endpoint = google.server_metadata.get('userinfo_endpoint')
        resp = google.get(userinfo_endpoint)
        user_info = resp.json()
        session['user'] = user_info
        return redirect(url_for('agent_interface'))
    except Exception as e:
        app.logger.error(f"OAuth error: {str(e)}")
        return render_template('error.html', error=f"Authentication error: {str(e)}. Please try again.")

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/agent')
@login_required
def agent_interface():
    # Pass query history to the template
    return render_template('agent.html', history=session.get('query_history', []))

@app.route('/submit_query', methods=['POST'])
@login_required
def submit_query():
    query = request.form.get('query')
    if query:
        result = call_agent(query)
        # Escape backticks and other special characters for JavaScript
        result = result.replace('\\', '\\\\').replace('`', '\\`')
        
        # Store query and result in session history
        if 'query_history' not in session:
            session['query_history'] = []
        
        # Add new query to the beginning of the list (most recent first)
        session['query_history'].insert(0, {
            'query': query,
            'result': result,
            'timestamp': import_datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        # Limit history to 20 items
        if len(session['query_history']) > 20:
            session['query_history'] = session['query_history'][:20]
            
        # Make sure session is saved
        session.modified = True
        
        return render_template('agent.html', result=result, query=query, history=session.get('query_history', []))
    return redirect(url_for('agent_interface'))

@app.route('/start_adk_web')
@login_required
def start_adk_web():
    try:
        subprocess.Popen(["adk", "web"], shell=True)
        return "ADK Web started successfully. <a href='/agent'>Go to Agent Interface</a>"
    except Exception as e:
        return f"Error starting ADK Web: {str(e)}"

@app.route('/clear_history', methods=['POST'])
@login_required
def clear_history():
    # Clear the query history from the session
    if 'query_history' in session:
        session.pop('query_history')
        session.modified = True
    return '', 204  # Return no content with 204 status code

if __name__ == '__main__':
    if not os.getenv('GOOGLE_CLIENT_ID') or not os.getenv('GOOGLE_CLIENT_SECRET'):
        print("Warning: GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables are required")
        print("Please set them before running the application")
    
    # Make sure the secret key is consistent across restarts
    if os.getenv('SECRET_KEY') is None:
        print("Warning: SECRET_KEY environment variable not set. Using a random key (sessions will be lost on restart)")
    
    app.run(debug=True, host='0.0.0.0', port=5000) 
