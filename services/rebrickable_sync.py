import requests
from typing import Optional, List, Dict, Any, Tuple
from models.database import db
from models.lego_set import LegoSetDefinition, UserLegoSet
from models.theme import Theme
from models.user import User
from config.rebrickable import API_BASE, API_KEY
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RebrickableAPI:
    def __init__(self):
        self.base_url = API_BASE
        self.headers = {
            "Authorization": f"key {API_KEY}",
            "Accept": "application/json"
        }

    def _make_request(self, url: str, method: str = "GET") -> Optional[Dict]:
        """Make API request with error handling"""
        try:
            response = requests.request(method, url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            return None

    def get_themes(self) -> List[Dict[str, Any]]:
        """Fetch all themes from Rebrickable API"""
        themes = []
        next_url = f"{self.base_url}/lego/themes/"
        
        while next_url:
            data = self._make_request(next_url)
            if not data:
                break
            
            themes.extend(data['results'])
            next_url = data.get('next')
            logger.info(f"Retrieved {len(themes)} themes so far...")
            
        return themes

    def get_user_sets(self, token: str) -> List[Tuple[str, bool, bool]]:
        """Fetch user's sets from Rebrickable"""
        url = f"{self.base_url}/users/{token}/sets/"
        data = self._make_request(url)
        
        if not data:
            return []
            
        return [(set['set']['set_num'], True, False) for set in data['results']]

    def get_set_details(self, set_num: str) -> Optional[Dict]:
        """Fetch detailed information about a specific set"""
        url = f"{self.base_url}/lego/sets/{set_num}/"
        return self._make_request(url)

class DatabaseManager:
    @staticmethod
    def sync_themes(themes: List[Dict]) -> None:
        """Synchronize themes with database"""
        logger.info("Starting theme synchronization...")
        
        for theme_data in themes:
            try:
                existing = Theme.query.get(theme_data['id'])
                
                if existing:
                    existing.name = theme_data['name']
                    existing.parent_id = theme_data['parent_id']
                    logger.debug(f"Updated theme: {existing.name}")
                else:
                    theme = Theme(
                        id=theme_data['id'],
                        name=theme_data['name'],
                        parent_id=theme_data['parent_id']
                    )
                    db.session.add(theme)
                    logger.debug(f"Added new theme: {theme.name}")
                
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error processing theme {theme_data['name']}: {str(e)}")

    @staticmethod
    def sync_set_definition(set_num: str, details: Dict) -> Optional[LegoSetDefinition]:
        """Sync a single set definition"""
        try:
            set_def = LegoSetDefinition.query.filter_by(set_number=set_num).first()
            
            if not set_def:
                set_def = LegoSetDefinition(set_number=set_num)
                db.session.add(set_def)
            
            set_def.name = details['name']
            set_def.piece_count = details['num_parts']
            set_def.year_released = details['year']
            set_def.theme_id = details['theme_id']
            set_def.image_url = details.get('set_img_url')
            
            db.session.commit()
            return set_def
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error syncing set definition {set_num}: {str(e)}")
            return None

def sync_user_collection(user: User) -> bool:
    """
    Synchronize user's collection with Rebrickable
    Returns True if successful, False otherwise
    """
    if not user or not user.id:
        logger.error("Invalid user object provided")
        return False

    if not user.rebrickable_token or not user.rebrickable_username:
        logger.error("User not connected to Rebrickable")
        return False

    api = RebrickableAPI()
    
    try:
        # Sync themes first
        logger.info("Fetching themes...")
        themes = api.get_themes()
        DatabaseManager.sync_themes(themes)
        
        # Get user's sets
        logger.info("Fetching user's sets...")
        sets = api.get_user_sets(user.rebrickable_token)
        logger.info(f"Found {len(sets)} sets in user's collection")
        
        # Process each set
        for set_num, owned, wanted in sets:
            logger.info(f"Processing set {set_num}")
            
            # Get or create set definition
            set_def = LegoSetDefinition.query.filter_by(set_number=set_num).first()
            
            if not set_def:
                details = api.get_set_details(set_num)
                if not details:
                    logger.warning(f"Could not fetch details for set {set_num}")
                    continue
                    
                set_def = DatabaseManager.sync_set_definition(set_num, details)
                if not set_def:
                    continue

            # Update user's association with this set
            try:
                user_set = UserLegoSet.query.filter_by(
                    user_id=user.id,
                    set_definition_id=set_def.id
                ).first()
                
                if not user_set:
                    user_set = UserLegoSet(
                        user_id=user.id,
                        set_definition_id=set_def.id
                    )
                    db.session.add(user_set)
                
                user_set.owned = owned
                user_set.wanted = wanted
                db.session.commit()
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error processing user set {set_num}: {str(e)}")
                continue

        logger.info("Sync completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Sync failed: {str(e)}")
        return False
