import requests
import os
import sys
# Add parent directory to path so we can import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import db, LegoSet, app

# Replace with your Rebrickable API key
API_KEY = "13d230bf1bed61b2260826ad9397495f"

def generate_user_token(api_key, username, password):
    """
    Generate a user token using the Rebrickable API.

    :param api_key: Your Rebrickable API key.
    :param username: The username of the Rebrickable user.
    :param password: The password of the Rebrickable user.
    :return: User token if successful, or an error message.
    """
    base_url = "https://rebrickable.com/api/v3/users/_token/"

    headers = {
        "Authorization": f"key {api_key}"
    }

    data = {
        "username": username,
        "password": password
    }

    try:
        response = requests.post(base_url, headers=headers, data=data)
        response.raise_for_status()  # Raise HTTPError for bad responses
        return response.json().get("user_token")

    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def get_user_set_list(api_key, user_token):
    """
    Fetch the user's set list from the Rebrickable API.

    :param api_key: Your Rebrickable API key.
    :param user_token: The user's token for authentication.
    :return: List of setlists if successful, or an error message.
    """
    base_url = "https://rebrickable.com/api/v3/users/{user_token}/setlists/".format(user_token=user_token)
    
    headers = {
        "Authorization": f"key {api_key}"
    }

    try:
        response = requests.get(base_url, headers=headers)
        response.raise_for_status()  # Raise HTTPError for bad responses
        return response.json()  # Parse and return the JSON response

    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def get_sets_in_setlist(api_key, user_token, setlist_id):
    """
    Fetch the sets in a specific setlist from the Rebrickable API.

    :param api_key: Your Rebrickable API key.
    :param user_token: The user's token for authentication.
    :param setlist_id: The ID of the setlist to fetch sets from.
    :return: List of sets if successful, or an error message.
    """
    base_url = "https://rebrickable.com/api/v3/users/{user_token}/setlists/{setlist_id}/sets/".format(user_token=user_token, setlist_id=setlist_id)

    headers = {
        "Authorization": f"key {api_key}"
    }

    try:
        response = requests.get(base_url, headers=headers)
        response.raise_for_status()  # Raise HTTPError for bad responses
        return response.json()  # Parse and return the JSON response

    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def add_set_to_database(set_data, owned=True):
    """
    Add or update a set in the database
    """
    with app.app_context():
        set_info = set_data.get('set', {})
        set_num = set_info.get('set_num')
        
        if not set_num:
            print(f"Skipping set with missing set number: {set_data}")
            return

        existing_set = LegoSet.query.filter_by(set_number=set_num).first()
        
        if existing_set:
            # Update existing set
            existing_set.name = set_info.get('name', existing_set.name)
            existing_set.owned = owned
            existing_set.image_url = set_info.get('set_img_url', existing_set.image_url)
            print(f"Updated set {set_num} in database")
        else:
            # Create new set
            new_set = LegoSet(
                set_number=set_num,
                name=set_info.get('name', 'Unknown Set'),
                piece_count=set_info.get('num_parts'),
                theme=set_info.get('theme_id'),
                year_released=set_info.get('year'),
                image_url=set_info.get('set_img_url'),
                owned=owned,
                wanted=not owned
            )
            db.session.add(new_set)
            print(f"Added new set {set_num} to database")
        
        try:
            db.session.commit()
        except Exception as e:
            print(f"Error saving set {set_num}: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    # Replace with your Rebrickable credentials
    USERNAME = "spacesnotabs"
    PASSWORD = "Raptor23"

    # Generate user token
    user_token = generate_user_token(API_KEY, USERNAME, PASSWORD)

    if isinstance(user_token, dict) and "error" in user_token:
        print(f"Error generating user token: {user_token['error']}")
    else:
        print(f"User token generated: {user_token}")

        # Fetch the set list using the generated token
        setlist_result = get_user_set_list(API_KEY, user_token)

        if "error" in setlist_result:
            print(f"Error fetching set list: {setlist_result['error']}")
        else:
            print("User's Set Lists:")
            for setlist in setlist_result.get("results", []):
                print(f"Setlist ID: {setlist['id']}, Name: {setlist['name']}, Num Sets: {setlist['num_sets']}")

                # Fetch sets in the current setlist
                sets_result = get_sets_in_setlist(API_KEY, user_token, setlist['id'])
                if "error" in sets_result:
                    print(f"Error fetching sets for setlist {setlist['id']}: {sets_result['error']}")
                else:
                    #print(sets_result)
                    print(f"Sets in Setlist '{setlist['name']}':")
                    for set_item in sets_result.get("results", []):
                        try:
                            set_info = set_item.get('set', {})
                            print(f"  Set ID: {set_info.get('set_num', 'Unknown')}, "
                                  f"Name: {set_info.get('name', 'Unknown')}, "
                                  f"Quantity: {set_item.get('quantity', 0)}")
                            add_set_to_database(set_item, owned=True)
                        except Exception as e:
                            print(f"Error processing set: {str(e)}")
