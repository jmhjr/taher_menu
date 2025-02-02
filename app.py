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


def get_taher_token():
    """Retrieve a fresh token if expired or not set."""
    global TAHER_API_TOKEN, TOKEN_EXPIRATION_TIME

    # If token exists and is still valid, return it
    if TAHER_API_TOKEN and TOKEN_EXPIRATION_TIME and datetime.utcnow() < TOKEN_EXPIRATION_TIME:
        return TAHER_API_TOKEN

    # Otherwise, request a new token (Modify based on how you obtain tokens)
    logging.info("Fetching new Taher API token...")

    # Placeholder: Modify this logic to obtain a fresh token from the API
    new_token = "NewGeneratedTokenHere"

    # Set token and expiration time (Assuming tokens are valid for 60 minutes)
    TAHER_API_TOKEN = new_token
    TOKEN_EXPIRATION_TIME = datetime.utcnow() + timedelta(minutes=60)

    logging.info(f"New Token Acquired: {TAHER_API_TOKEN}")
    return TAHER_API_TOKEN


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
        "Authorization": f"Bearer {get_taher_token()}"  # Use dynamically fetched token
    }

    payload = {
        "request": {
            "Token": get_taher_token(),  # Use fresh token
            "Version": "100256",
            "Username": "22FC8A67-7663-43D5-B752-615937EA2A2C@tehda.com",
            "UserId": "190636b1-46d4-4987-b06d-ff0dc6707e6e",
            "AppIdentifier": "TAHER",
            "ItemType": "MenuItem",
            "LocalizationContext": "en-US",
            "StartDate": "2025-01-27",
            "EndDate": "2025-02-17",
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

        # If token is invalid, refresh and retry once
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

                    # Exclude "FILL IN SPECIAL" and items with "milk"
                    if item_name != "FILL IN SPECIAL" and "milk" not in item_name.lower() and "Lunch" in category_name:
                        if formatted_date not in grouped_items:
                            grouped_items[formatted_date] = []
                        grouped_items[formatted_date].append(item_name)
                        seen_items_by_date.setdefault(formatted_date, set()).add(item_name)

        # HTML output
        background_image_url = "https://i.imgur.com/g1JUN3V.jpeg"  # Change to your actual background

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
                }}
                h1 {{
                    text-align: center;
                    font-size: 36px;
                    font-weight: bold;
                }}
                strong {{
                    color: #FFD700;  /* Gold color */
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


if __name__ == "__main__":
    app.run(debug=True)  # Enable debug mode for Flask
