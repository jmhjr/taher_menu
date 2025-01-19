import json
import requests
import werkzeug
from flask import Flask, jsonify

app = Flask(__name__)

# Default route to handle root URL (/)
@app.route("/", methods=["GET"])
def home():
    return "Welcome to the Taher Menu API. Visit /lunch-menu to fetch the menu.", 200

@app.route('/lunch-menu', methods=['GET'])
def lunch-menu():
    taher_api_url = "https://engage-prd-api.enbrec.net/genericitem/items"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Taher/100256 CFNetwork/3826.400.110 Darwin/24.3.0"
    }
    payload = {
        "request": {
            "Token": r"Z3Z9ODCgh9H8TAdXgxYRr8gOeVyp69bkHa2qPYPWvNWUItDvMYFnXCFHcFHSRaTWLArEc8pyvV2JSl\/fHGVoLeELR1sU3RhKHVx8vCpWFzfJyFE3XDtNoyITC8udWJQpbulZ+6RhE7ROSQfWtxA3nm6tHP85cmSkvTlA2W+A4BhsXMy\/naXqh7nnjJCS+6y1aq8pl855ggsB4ZMHOusuoZTw0dLspW\/gCaDKKE4Pko4s7GEy6vzIHatiD5SZ\/Ti49ixPkaOemd+fuhAsDqEz5KBEmQU7FR+xzhTR6E8nODWiikS08eSSGPs+oBRofmWRLXZOKmLVtfQakQoKcPrWtw==",
            "Version": "100256",
            "Username": "hunkinsj@gmail.com",
            "UserId": "06b9e022-726c-4886-84ea-b429a6086e75",
            "AppIdentifier": "TAHER",
            "ItemType": "MenuItem",
            "LocalizationContext": "en-US",
            "StartDate": "2025-01-19",
            "EndDate": "2025-02-17",
            "Platform": "iPhone",
            "LocationID": "d7b68811-441b-4379-a279-3d96e68cfc2f"
        }
    }

    try:
        # Send request to the Taher API
        response = requests.post(taher_api_url, headers=headers, json=payload)
        logging.info(f"API Response Status Code: {response.status_code}")
        logging.info(f"API Response Content: {response.text}")

        # Raise an error for unsuccessful status codes
        response.raise_for_status()

        # Check if response is empty
        if not response.text.strip():
            return {"error": "API returned an empty response"}, 500

        # Parse the JSON response
        menu_data = response.json()
        return jsonify(menu_data)

    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        return {"error": f"Request failed: {e}"}, 500
    except ValueError as e:
        logging.error(f"Invalid JSON response: {e}")
        return {"error": f"Invalid JSON response: {e}"}, 500

