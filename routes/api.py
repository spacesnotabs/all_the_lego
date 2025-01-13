
from flask import Blueprint, request, jsonify
from models.database import db
from models.lego_set import LegoSet

api = Blueprint('api', __name__)

@api.route('/sets', methods=['GET'])
def get_sets():
    owned = request.args.get('owned', type=bool)
    wanted = request.args.get('wanted', type=bool)
    theme = request.args.get('theme')
    
    query = LegoSet.query
    if owned is not None:
        query = query.filter_by(owned=owned)
    elif wanted is not None:
        query = query.filter_by(wanted=wanted)
    if theme:
        query = query.filter_by(theme=theme)
    
    sets = query.all()
    return jsonify([s.to_dict() for s in sets])

@api.route('/sets', methods=['POST'])
def add_set():
    data = request.json
    lego_set = LegoSet(
        set_number=data['set_number'],
        name=data['name'],
        piece_count=data.get('piece_count'),
        theme=data.get('theme'),
        year_released=data.get('year_released'),
        owned=data.get('owned', False),
        wanted=data.get('wanted', False)
    )
    db.session.add(lego_set)
    
    try:
        db.session.commit()
        return jsonify(lego_set.to_dict()), 201
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