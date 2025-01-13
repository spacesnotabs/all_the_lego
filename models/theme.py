from .database import db

class Theme(db.Model):
    __tablename__ = 'theme'  # Explicitly set table name
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('theme.id'), nullable=True)
    
    parent = db.relationship('Theme', remote_side=[id], backref='children')
    
    def __repr__(self):
        return f'<Theme {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'parent_id': self.parent_id,
            'parent_name': self.parent.name if self.parent else None
        }