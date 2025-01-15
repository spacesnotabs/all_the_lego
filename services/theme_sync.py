
import requests
from models.database import db
from models.theme import Theme
from config.rebrickable import API_KEY

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
    # Create tables if they don't exist
    db.create_all()
    
    themes = get_all_themes()
    print(f"Retrieved {len(themes)} themes from API")
    
    for theme_data in themes:
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