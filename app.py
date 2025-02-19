import logging
import json
import requests
from datetime import datetime, timedelta
from flask import Flask, jsonify

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

app = Flask(__name__)

# Global variables to store token and expiration time
TAHER_API_TOKEN = None
TOKEN_EXPIRATION_TIME = None

# User credentials for authentication
USERNAME = "22FC8A67-7663-43D5-B752-615937EA2A2C@tehda.com"
PASSWORD = "Test1234"

def get_taher_token():
    """Retrieve a fresh token from the authentication endpoint if expired or not set."""
    global TAHER_API_TOKEN, TOKEN_EXPIRATION_TIME

    if TAHER_API_TOKEN and TOKEN_EXPIRATION_TIME and datetime.utcnow() < TOKEN_EXPIRATION_TIME:
        return TAHER_API_TOKEN

    logging.info("Fetching new Taher API token...")

    auth_url = "https://engage-prd-api.enbrec.net/authenticate/authenticateuser"

    auth_payload = {
        "AppIdentifier": "TAHER",
	    "Version": "100256",
	    "LocalizationContext": "en-US",
	    "Platform": "iPhone",
	    "Password": "Test1234",
	    "Username": "22FC8A67-7663-43D5-B752-615937EA2A2C@tehda.com"
    }

    auth_headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Taher/100256 CFNetwork/3826.400.110 Darwin/24.3.0"
    }

    try:
        response = requests.post(auth_url, json=auth_payload, headers=auth_headers)
        response.raise_for_status()

        auth_data = response.json()

        # Log the full response for debugging
        logging.info(f"Auth API Response: {json.dumps(auth_data, indent=2)}")

        # Extract token (modify this based on actual API response structure)
        new_token = auth_data.get("Data", {}).get("Token")  # Try different keys if this is None

        if not new_token:
            logging.error("Failed to retrieve token: No token found in response")
            return None

        # Set token and expiration time
        TAHER_API_TOKEN = new_token
        TOKEN_EXPIRATION_TIME = datetime.utcnow() + timedelta(minutes=60)

        logging.info(f"New Token Acquired: {TAHER_API_TOKEN}")
        return TAHER_API_TOKEN

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to get token: {e}")
        return None

@app.route("/", methods=["GET"])
def home():
    return "Welcome to the Taher Menu API. Visit /lunch_menu to fetch the menu.", 200

@app.route('/lunch_menu', methods=['GET'])
def lunch_menu():
    taher_api_url = "https://engage-prd-api.enbrec.net/genericitem/items"

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Taher/100256 CFNetwork/3826.400.110 Darwin/24.3.0",
        "Authorization": f"Bearer {get_taher_token()}"
    }

    payload = {
        "request": {
            "Token": get_taher_token(),
            "Version": "100256",
            "Username": USERNAME,
            "UserId": "190636b1-46d4-4987-b06d-ff0dc6707e6e",
            "AppIdentifier": "TAHER",
            "ItemType": "MenuItem",
            "LocalizationContext": "en-US",
            "StartDate": "2025-01-27",
            "EndDate": "2026-02-17",
            "Platform": "iPhone",
            "LocationID": "d7b68811-441b-4379-a279-3d96e68cfc2f"
        }
    }

    logging.info("Sending request to Taher API")

    def format_taher_date(date_string):
        timestamp = int(date_string.strip("/Date()/")) / 1000
        date = datetime.utcfromtimestamp(timestamp)
        return date.strftime("%B %d, %Y (%A)")

    try:
        response = requests.post(taher_api_url, headers=headers, json=payload)

        if response.status_code == 403:
            logging.warning("403 Forbidden - Token may be expired. Fetching new token...")
            headers["Authorization"] = f"Bearer {get_taher_token()}"
            payload["request"]["Token"] = get_taher_token()
            response = requests.post(taher_api_url, headers=headers, json=payload)

        response.raise_for_status()

        if not response.text.strip():
            return {"error": "API returned an empty response"}, 500

        menu_data = response.json()
        today = datetime.utcnow()
        end_date = today + timedelta(days=10)

        grouped_items = {}
        seen_items_by_date = {}

        for item in menu_data.get("Data", {}).get("Items", []):
            if "EventDateUTC" in item:
                timestamp = int(item["EventDateUTC"].strip("/Date()/")) / 1000
                event_date = datetime.utcfromtimestamp(timestamp)

                if today.date() <= event_date.date() <= end_date.date():
                    category_name = item.get("MetaData", {}).get("CategoryName", "Unknown Category")
                    formatted_date = format_taher_date(item["EventDateUTC"])
                    item_name = item.get("Name", "Unnamed Item")

                    if item_name != "FILL IN SPECIAL" and "milk" not in item_name.lower() and "Lunch" in category_name:
                        if formatted_date not in grouped_items:
                            grouped_items[formatted_date] = []
                        grouped_items[formatted_date].append(item_name)
                        seen_items_by_date.setdefault(formatted_date, set()).add(item_name)

        background_image_url = "https://i.imgur.com/g1JUN3V.jpeg"

        formatted_output = f"""
        <html>
        <head>
            <style>
                body {{
                    background-image: url('{background_image_url}');
                    background-size: cover;
                    background-position: center;
                    color: white;
                    font-family: Arial, sans-serif;
                    padding: 20px;
		    overflow-y: scroll; /* Ensures the content is scrollable */
                }}
		/* Hide vertical scrollbar, but keep the ability to scroll */
		body::-webkit-scrollbar {{
		    width: 0px; /* Hides the scrollbar */
		    background: transparent; /* Optional: makes background transparent */
		    }}
                h1 {{
                    text-align: center;
                    font-size: 36px;
                    font-weight: bold;
                }}
                strong {{
                    color: #FFD700;
                }}
                .menu-item {{
                    margin-left: 20px;
                    list-style-type: disc;
                    margin-bottom: 5px;
                }}
            </style>
        </head>
        <body>
            <h1>Lunch Menu</h1>
            <div>
        """

        for date, items in grouped_items.items():
            if items:
                formatted_output += f"<strong>{date} - Lunch</strong><br>"
                formatted_output += "<ul>" + "".join([f"<li class='menu-item'>{item}</li>" for item in items]) + "</ul>"

        formatted_output += """
            </div>
        </body>
        </html>
        """

        return formatted_output, 200

    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        return {"error": f"Request failed: {e}"}, 500

    except ValueError as e:
        logging.error(f"Invalid JSON response: {e}")
        return {"error": f"Invalid JSON response: {e}"}, 500
