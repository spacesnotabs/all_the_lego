from flask import Flask, render_template
from flask_migrate import Migrate
from authlib.integrations.flask_client import OAuth
from models.theme import Theme
from models.lego_set import LegoSetDefinition, UserLegoSet
from models.database import db
from models.user import User  # Make sure to import User model
from routes.api import api
from routes.auth import auth_bp
import os
from dotenv import load_dotenv
from config.logging_config import setup_logging

load_dotenv()

def ensure_database_exists(app):
    """Ensure all database tables exist"""
    with app.app_context():
        # Check if database needs to be initialized
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        if not existing_tables:
            print("No tables found. Creating database schema...")
            db.create_all()
            print("Database tables created successfully")
        else:
            print(f"Found existing tables: {', '.join(existing_tables)}")

def create_app():
    # Set up logging first
    setup_logging()
    
    app = Flask(__name__)
    
    # Configure database
    db_dir = os.path.join(os.path.dirname(__file__), 'database')
    os.makedirs(db_dir, exist_ok=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(db_dir, "lego_collection.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'your-secret-key'
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    
    # Ensure database and tables exist
    ensure_database_exists(app)
    
    # OAuth Configuration
    app.secret_key = os.getenv('SECRET_KEY', os.urandom(24))
    app.config['GOOGLE_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID')
    app.config['GOOGLE_CLIENT_SECRET'] = os.getenv('GOOGLE_CLIENT_SECRET')
    app.config['GOOGLE_DISCOVERY_URL'] = os.getenv('GOOGLE_DISCOVERY_URL')
    app.config['DEBUG'] = True
    app.config['ENV'] = 'development'

    
    # Initialize OAuth
    oauth = OAuth()
    oauth.init_app(app)
    oauth.register(
        name='google',
        server_metadata_url=app.config['GOOGLE_DISCOVERY_URL'],
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        client_kwargs={
            'scope': 'openid email profile',
            'prompt': 'select_account'
        }
    )
    
    # Register blueprints
    app.register_blueprint(api, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    

    @app.route('/')
    def index():
        return render_template('index.html')
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, ssl_context=('cert.pem', 'key.pem'))
