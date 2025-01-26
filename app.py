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
        "Cookie": "ARRAffinity=e36ab3397b6b1b3b97e7bb70f5e412024ab9f5606858d16ad326e2d5d5115664; "
                  "ARRAffinitySameSite=e36ab3397b6b1b3b97e7bb70f5e412024ab9f5606858d16ad326e2d5d5115664"
    }

    payload = {
        "request": {
            "Token": r"MyYkXV6FsdlQqOQwqG1F86Py4C6sDmr7jT0BXDgE0i/nSSt2pti1DQpWB36O3NoJjDjqZYOztjktzt+sM6nhjP9CqodPtw4yvCxznhpe0YZA15CxBXbshSfysv5yV3iaKVrOwKmFqZDEToY0y6e2s+0zEuAsAsBzBPlD77OwzzIPxY/Be6g+Wz7LT7ZTEFmxOMHT1KoDI8YgeAJMHUiotFXEI5H1r76cYMG8375qTNKlhlVHFBIRiKLUB7sHiqrfukNSnLNVg6cY0MQfXfksGI/8QjHigEhjoqNAWBFLjCPzRsPaxQgnByagHtzBb/RCbSjIShHbmYAzUWZrEBb+GYd7iIOUfX9t5SKq+xJEcZY=",
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
    logging.info(f"Request URL: {taher_api_url}")
    logging.info(f"Request Headers: {headers}")
    logging.info(f"Request Payload: {json.dumps(payload, indent=2)}")

    def format_taher_date(date_string, category_name):
        timestamp = int(date_string.strip("/Date()/")) / 1000
        date = datetime.utcfromtimestamp(timestamp)
        formatted_date = date.strftime("%B %d, %A")
        return f"{formatted_date} - {category_name}"

    try:
        response = requests.post(taher_api_url, headers=headers, json=payload)
        logging.info(f"API Response Status Code: {response.status_code}")
        logging.info(f"API Response Content: {response.text}")

        response.raise_for_status()

        if not response.text.strip():
            return {"error": "API returned an empty response"}, 500

        menu_data = response.json()
        today = datetime.utcnow()
        end_date = today + timedelta(days=2)

        filtered_items = []
        seen_items = set()  # To keep track of item names and avoid duplicates
        for item in menu_data.get("Data", {}).get("Items", []):
            if "EventDateUTC" in item:
                timestamp = int(item["EventDateUTC"].strip("/Date()/")) / 1000
                event_date = datetime.utcfromtimestamp(timestamp)

                if today.date() <= event_date.date() <= end_date.date():
                    category_name = item.get("MetaData", {}).get("CategoryName", "Unknown Category")
                    formatted_date = format_taher_date(item["EventDateUTC"], category_name)
                    item_name = item.get("Name", "Unnamed Item")
                    
                    # Filter out unwanted items and duplicates
                    if item_name != "FILL IN SPECIAL" and item_name not in seen_items:
                        filtered_items.append({
                            "FormattedDate": formatted_date,
                            "name": item_name
                        })
                        seen_items.add(item_name)  # Mark the item as seen

        return jsonify(filtered_items)

    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        return {"error": f"Request failed: {e}"}, 500

    except ValueError as e:
        logging.error(f"Invalid JSON response: {e}")
        return {"error": f"Invalid JSON response: {e}"}, 500
