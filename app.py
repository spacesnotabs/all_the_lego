# app.py
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Ensure the database directory exists
db_dir = os.path.join(os.path.dirname(__file__), 'database')
os.makedirs(db_dir, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(db_dir, "lego_collection.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class LegoSet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    set_number = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    piece_count = db.Column(db.Integer)
    theme = db.Column(db.String(100))
    year_released = db.Column(db.Integer)
    owned = db.Column(db.Boolean, default=False)
    wanted = db.Column(db.Boolean, default=False)
    image_url = db.Column(db.String(500))
    last_price_check = db.Column(db.DateTime)
    current_price = db.Column(db.Float)
    
    def to_dict(self):
        return {
            'id': self.id,
            'set_number': self.set_number,
            'name': self.name,
            'piece_count': self.piece_count,
            'theme': self.theme,
            'year_released': self.year_released,
            'owned': self.owned,
            'wanted': self.wanted,
            'image_url': self.image_url,
            'current_price': self.current_price,
            'last_price_check': self.last_price_check.isoformat() if self.last_price_check else None
        }

def create_tables():
    with app.app_context():
        db.create_all()

@app.before_request
def initialize_database():
    create_tables()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/sets', methods=['GET'])
def get_sets():
    owned = request.args.get('owned', type=bool)
    wanted = request.args.get('wanted', type=bool)
    
    query = LegoSet.query
    if owned is not None:
        query = query.filter_by(owned=owned)
    if wanted is not None:
        query = query.filter_by(wanted=wanted)
        
    sets = query.all()
    return jsonify([s.to_dict() for s in sets])

@app.route('/api/sets', methods=['POST'])
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

@app.route('/api/sets/<int:set_id>', methods=['PUT'])
def update_set(set_id):
    lego_set = LegoSet.query.get_or_404(set_id)
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

@app.route('/api/sets/<int:set_id>', methods=['DELETE'])
def delete_set(set_id):
    lego_set = LegoSet.query.get_or_404(set_id)
    db.session.delete(lego_set)
    db.session.commit()
    return '', 204

@app.route('/initdb')
def initdb():
    create_tables()
    return 'Database initialized!'

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)