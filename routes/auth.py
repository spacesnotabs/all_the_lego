from flask import Blueprint, url_for, session, redirect, current_app
import secrets
from models.user import User
from models.database import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login')
def login():
    google = current_app.extensions['authlib.integrations.flask_client'].google
    redirect_uri = url_for('auth.callback', _external=True)
    # Generate and store nonce
    session['nonce'] = secrets.token_urlsafe(16)
    return google.authorize_redirect(redirect_uri, nonce=session['nonce'])

@auth_bp.route('/callback')
def callback():
    google = current_app.extensions['authlib.integrations.flask_client'].google
    token = google.authorize_access_token()
    # Pass the stored nonce to parse_id_token
    nonce = session.pop('nonce', None)
    user_info = google.parse_id_token(token, nonce=nonce)
    session['user_info'] = user_info
    
    # Check if user exists
    user = User.query.filter_by(google_id=user_info['sub']).first()
    if not user:
        user = User(
            google_id=user_info['sub'],
            email=user_info['email'],
            name=user_info.get('name', '')
        )
        db.session.add(user)
        db.session.commit()
    
    session['user_id'] = user.id
    return redirect('/')

@auth_bp.route('/logout')
def logout():
    session.pop('user_info', None)
    return redirect('/')