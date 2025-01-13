from .database import db
from datetime import datetime

class LegoSet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    set_number = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    piece_count = db.Column(db.Integer)
    theme_id = db.Column(db.Integer, db.ForeignKey('theme.id'))
    theme = db.relationship('Theme', backref='sets')
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
            'theme_id': self.theme_id,
            'theme': self.theme.name if self.theme else None,
            'year_released': self.year_released,
            'owned': self.owned,
            'wanted': self.wanted,
            'image_url': self.image_url,
            'current_price': self.current_price,
            'last_price_check': self.last_price_check.isoformat() if self.last_price_check else None
        }