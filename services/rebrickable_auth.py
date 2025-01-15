import requests
from config.rebrickable import API_BASE, API_KEY
import logging

logger = logging.getLogger(__name__)

def generate_user_token(username: str, password: str) -> str:
    """Generate a user token from Rebrickable credentials"""
    url = f"{API_BASE}/users/_token/"
    headers = {
        "Authorization": f"key {API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    # Switch to form data instead of JSON
    data = {
        "username": username,
        "password": password
    }
    
    try:
        # Use data parameter instead of json for form-encoded
        response = requests.post(url, headers=headers, data=data)
        
        # Add detailed error logging
        if response.status_code != 200:
            logger.error(f"Status Code: {response.status_code}")
            logger.error(f"Response Text: {response.text}")
            logger.error(f"Request URL: {url}")
            logger.error(f"Request Headers: {headers}")
            return {"error": f"Authentication failed: {response.status_code}"}
            
        response.raise_for_status()
        return response.json().get('user_token')
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to generate user token: {str(e)}")
        return {"error": "Failed to authenticate with Rebrickable"}
