from models.database import db
from datetime import datetime

class LegoSetDefinition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    set_number = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    piece_count = db.Column(db.Integer)
    theme_id = db.Column(db.Integer, db.ForeignKey('theme.id'))
    year_released = db.Column(db.Integer)
    image_url = db.Column(db.String(500))

class UserLegoSet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    set_definition_id = db.Column(db.Integer, db.ForeignKey('lego_set_definition.id'), nullable=False)
    owned = db.Column(db.Boolean, default=False)
    wanted = db.Column(db.Boolean, default=False)
    custom_notes = db.Column(db.Text)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', back_populates='user_sets', lazy=True)
    set_definition = db.relationship('LegoSetDefinition')

    def to_dict(self):
        return {
            'id': self.id,
            'set_number': self.set_definition.set_number,
            'name': self.set_definition.name,
            'piece_count': self.set_definition.piece_count,
            'theme_id': self.set_definition.theme_id,
            'year_released': self.set_definition.year_released,
            'image_url': self.set_definition.image_url,
            'owned': self.owned,
            'wanted': self.wanted,
            'custom_notes': self.custom_notes,
            'date_added': self.date_added.isoformat()
        }