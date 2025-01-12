# scraper.py
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import LegoSet, db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LegoScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    def get_set_info(self, set_number):
        """
        Scrapes information for a specific LEGO set from popular LEGO marketplaces.
        Note: This is a simplified example. You'll need to adapt it to specific websites.
        """
        try:
            # Example URL - replace with actual marketplace URL
            url = f"https://example-lego-marketplace.com/sets/{set_number}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # These selectors would need to be adjusted based on the actual website
            price = self._extract_price(soup)
            image_url = self._extract_image(soup)
            name = self._extract_name(soup)
            
            return {
                'price': price,
                'image_url': image_url,
                'name': name,
                'last_checked': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error scraping set {set_number}: {str(e)}")
            return None
    
    def _extract_price(self, soup):
        """Extract price from the page - adjust selectors as needed"""
        try:
            price_elem = soup.select_one('.price-selector')
            if price_elem:
                price_text = price_elem.text.strip()
                return float(price_text.replace('$', '').replace(',', ''))
        except Exception as e:
            logger.error(f"Error extracting price: {str(e)}")
        return None
    
    def _extract_image(self, soup):
        """Extract image URL - adjust selectors as needed"""
        try:
            img_elem = soup.select_one('.product-image-selector')
            if img_elem and 'src' in img_elem.attrs:
                return img_elem['src']
        except Exception as e:
            logger.error(f"Error extracting image: {str(e)}")
        return None
    
    def _extract_name(self, soup):
        """Extract set name - adjust selectors as needed"""
        try:
            name_elem = soup.select_one('.product-name-selector')
            if name_elem:
                return name_elem.text.strip()
        except Exception as e:
            logger.error(f"Error extracting name: {str(e)}")
        return None

def update_prices():
    """
    Updates prices for all sets in the database that are marked as wanted
    """
    scraper = LegoScraper()
    wanted_sets = LegoSet.query.filter_by(wanted=True).all()
    
    for lego_set in wanted_sets:
        logger.info(f"Updating information for set {lego_set.set_number}")
        
        info = scraper.get_set_info(lego_set.set_number)
        if info and info['price']:
            lego_set.current_price = info['price']
            lego_set.last_price_check = info['last_checked']
            
            # Update image URL if not already set
            if not lego_set.image_url and info['image_url']:
                lego_set.image_url = info['image_url']
            
            # Update name if not already set
            if not lego_set.name and info['name']:
                lego_set.name = info['name']
                
            try:
                db.session.commit()
                logger.info(f"Successfully updated set {lego_set.set_number}")
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error saving updates for set {lego_set.set_number}: {str(e)}")
        
        # Be nice to the server
        time.sleep(2)

if __name__ == '__main__':
    # This allows the script to be run independently to update prices
    from app import app
    with app.app_context():
        update_prices()