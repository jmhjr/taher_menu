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
def get_menu():
    # Taher API URL
    taher_api_url = "https://engage-prd-api.enbrec.net/genericitem/items"
    
    # Headers captured from Charles
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Taher/100256 CFNetwork/3826.400.110 Darwin/24.3.0",
        "Host": "engage-prd-api.enbrec.net"
    }
    
    # JSON payload captured from Charles
    payload = {
        "request": {
            "Token": "Z3Z9ODCgh9H8TAdXgxYRr8gOeVyp69bkHa2qPYPWvNWUItDvMYFnXCFHcFHSRaTWLAr...",
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
        # Send POST request to Taher API
        response = requests.post(taher_api_url, headers=headers, json=payload)
        response_data = response.json()
        
        # Simplify the response for Dakboard
        dakboard_data = {
            "menu": [
                {
                    "date": item["date"],
                    "items": [
                        {"name": menu["name"], "description": menu["description"]}
                        for menu in item["items"]
                    ]
                } for item in response_data["menu"]
            ]
        }
        
        # Return simplified data
        return jsonify(dakboard_data)
    
    except Exception as e:
        # Handle errors
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(debug=True)

