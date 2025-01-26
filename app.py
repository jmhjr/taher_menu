from flask import Flask, jsonify
from datetime import datetime, timedelta
import requests
import logging

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
            "Token": r"MyTokenHere",
            "Version": "100256",
            "Username": "YourUsername",
            "UserId": "YourUserId",
            "AppIdentifier": "TAHER",
            "ItemType": "MenuItem",
            "LocalizationContext": "en-US",
            "StartDate": "2025-01-27",
            "EndDate": "2025-02-17",
            "Platform": "iPhone",
            "LocationID": "d7b68811-441b-4379-a279-3d96e68cfc2f"
        }
    }

    try:
        # Send request to the Taher API
        response = requests.post(taher_api_url, headers=headers, json=payload)
        response.raise_for_status()
        menu_data = response.json()

        # Extract only the "Items" section
        items = menu_data.get("Data", {}).get("Items", [])

        # Format the items to include only the "Name" and any other desired fields
        filtered_items = [
            {
                "Name": item.get("Name"),
                "FormattedDate": item.get("FormattedDate"),
                "CategoryName": item.get("MetaData", {}).get("CategoryName"),
                "Calories": item.get("MetaData", {}).get("Calories"),
                "LargeImageURL": item.get("LargeImageURL"),
                "Station": item.get("MetaData", {}).get("Station")
            }
            for item in items
        ]

        # Return only the filtered items
        return jsonify({
            "Items": filtered_items
        })

    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        return {"error": f"Request failed: {e}"}, 500

    except ValueError as e:
        logging.error(f"Invalid JSON response: {e}")
        return {"error": f"Invalid JSON response: {e}"}, 500


# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)  # Enable debug mode for Flask
