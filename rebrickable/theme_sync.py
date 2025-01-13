import requests
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.database import db
from models.theme import Theme
from sqlalchemy.orm import Session

API_KEY = "13d230bf1bed61b2260826ad9397495f"

def get_theme(theme_id):
    """Fetch a single theme from Rebrickable API"""
    url = f"https://rebrickable.com/api/v3/lego/themes/{theme_id}/"
    headers = {
        "Accept": "application/json",
        "Authorization": f"key {API_KEY}"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

def get_all_themes():
    """Fetch all themes from Rebrickable API"""
    url = "https://rebrickable.com/api/v3/lego/themes/"
    headers = {
        "Accept": "application/json",
        "Authorization": f"key {API_KEY}"
    }
    
    themes = []
    next_url = url
    
    while next_url:
        response = requests.get(next_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            themes.extend(data['results'])
            next_url = data.get('next')
        else:
            print(f"Error fetching themes: {response.status_code}")
            break
            
    return themes

def sync_themes():
    """Synchronize themes with the database"""
    app = create_app()
    
    with app.app_context():
        # Ensure tables exist
        db.create_all()
        
        themes = get_all_themes()
        print(f"Retrieved {len(themes)} themes from API")
        
        for theme_data in themes:
            # Use get() on Session instead of Query
            existing = db.session.get(Theme, theme_data['id'])
            
            if not existing:
                theme = Theme(
                    id=theme_data['id'],
                    name=theme_data['name'],
                    parent_id=theme_data['parent_id']
                )
                db.session.add(theme)
                print(f"Added theme: {theme.name}")
            else:
                existing.name = theme_data['name']
                existing.parent_id = theme_data['parent_id']
                print(f"Updated theme: {existing.name}")
        
        try:
            db.session.commit()
            print(f"Successfully synchronized {len(themes)} themes")
        except Exception as e:
            db.session.rollback()
            print(f"Error synchronizing themes: {str(e)}")

if __name__ == "__main__":
    sync_themes()