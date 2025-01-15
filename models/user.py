from models.database import db

class User(db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100))
    rebrickable_username = db.Column(db.String(100))
    rebrickable_token = db.Column(db.String(100))
    
    user_sets = db.relationship('UserLegoSet', back_populates='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.email}>'