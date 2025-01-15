from flask import Blueprint, request, jsonify, session
from models.database import db
from models.lego_set import LegoSetDefinition, UserLegoSet
from models.user import User
from services.rebrickable_sync import sync_user_collection
from services.rebrickable_auth import generate_user_token
import logging

logger = logging.getLogger(__name__)

api = Blueprint('api', __name__)

@api.route('/sets', methods=['GET'])
def get_sets():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    query = UserLegoSet.query.filter_by(user_id=session['user_id'])
    
    if request.args.get('owned'):
        query = query.filter_by(owned=True)
    elif request.args.get('wanted'):
        query = query.filter_by(wanted=True)
        
    if theme := request.args.get('theme'):
        query = query.join(LegoSetDefinition).join(Theme).filter(Theme.name == theme)
    
    user_sets = query.all()
    return jsonify([s.to_dict() for s in user_sets])

@api.route('/sets', methods=['POST'])
def add_set():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json
    
    # First, find or create the set definition
    set_def = LegoSetDefinition.query.filter_by(set_number=data['set_number']).first()
    if not set_def:
        set_def = LegoSetDefinition(
            set_number=data['set_number'],
            name=data['name'],
            piece_count=data.get('piece_count'),
            theme_id=data.get('theme_id'),
            year_released=data.get('year_released')
        )
        db.session.add(set_def)
        
    # Then create the user's association with this set
    user_set = UserLegoSet(
        user_id=session['user_id'],
        set_definition=set_def,
        owned=data.get('owned', False),
        wanted=data.get('wanted', False)
    )
    db.session.add(user_set)
    
    try:
        db.session.commit()
        return jsonify(user_set.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@api.route('/sets/<int:set_id>', methods=['PUT', 'DELETE'])
def manage_set(set_id):
    lego_set = LegoSet.query.get_or_404(set_id)
    
    if request.method == 'DELETE':
        db.session.delete(lego_set)
        db.session.commit()
        return '', 204
        
    data = request.json
    for key, value in data.items():
        if hasattr(lego_set, key):
            setattr(lego_set, key, value)
    
    try:
        db.session.commit()
        return jsonify(lego_set.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@api.route('/rebrickable/status', methods=['GET'])
def get_rebrickable_status():
    if 'user_id' not in session:  # Just check if user is logged in to our app
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(session['user_id'])
    return jsonify({
        'connected': bool(user and user.rebrickable_username and user.rebrickable_token)
    })

@api.route('/rebrickable/connect', methods=['POST'])
def connect_rebrickable():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    print(f'connecting rebrickable for {username}, and {password}')
    try:
        user_token = generate_user_token(username, password)
        if isinstance(user_token, dict) and "error" in user_token:
            logger.error(f"Failed to connect Rebrickable for user {username}")
            return jsonify({'error': user_token['error']}), 400
        
        user = User.query.get(session['user_id'])
        if user:
            user.rebrickable_username = username
            user.rebrickable_token = user_token
            db.session.commit()
            logger.info(f"Successfully connected Rebrickable for user {username}")
            return jsonify({'success': True})
        
        return jsonify({'error': 'User not found'}), 404
        
    except Exception as e:
        logger.error(f"Error connecting Rebrickable: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api.route('/rebrickable/sync', methods=['POST'])
def sync_rebrickable():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    if not user.rebrickable_token or not user.rebrickable_username:
        return jsonify({'error': 'Not connected to Rebrickable'}), 400
    
    try:
        sync_user_collection(user)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500