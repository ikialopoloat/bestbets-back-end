import os
import requests

import firebase_admin
from firebase_admin import credentials
from firebase_admin import auth
from firebase_admin import exceptions

from flask import Flask, send_file, jsonify, render_template, request
from flask import redirect, url_for
app = Flask(__name__)

combined_teams_odds =[]

@app.route("/")
def index():
    try:
        cred = credentials.Certificate('src/serviceAccountKey.json') # <-- REPLACE WITH YOUR SERVICE ACCOUNT FILE PATH
        firebase_admin.initialize_app(cred)
        print("firebase initialized")
    except Exception as e:
        print("firebase not initialized:")
        print(e)
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html', error=None)

@app.route("/login")
def login():
    return render_template('login.html')

@app.route("/homepage")
def homepage():
 return render_template('homepage.html')



@app.route("/mainpage")
def mainpage():

    try:
        nrl_odds_data = get_nrl_odds(API_KEY, API_ENDPOINT)
        if nrl_odds_data:
            print("Successfully fetched NRL Rugby Odds:")
            print("sportsbet data:")
       
            for event in nrl_odds_data:
                for bookmaker in event['bookmakers']:
                    if bookmaker['key'] == 'sportsbet':
                        for market in bookmaker['markets']:
                            if market['key'] == 'h2h':
                                # Get home and away team data
                                home_team_name = market['outcomes'][0]['name']
                                home_team_odds = market['outcomes'][0]['price']
                                away_team_name = market['outcomes'][1]['name']
                                away_team_odds = market['outcomes'][1]['price']

                                # Append a tuple containing all four pieces of data to the combined list
                                combined_teams_odds.append((home_team_name, home_team_odds, away_team_name, away_team_odds))
                # You can now process and use the 'nrl_odds_data' as needed


                # For example, you could pass this data to a template or store it
            print("Combined Teams and Odds:", combined_teams_odds)

        return render_template('index.html', data=combined_teams_odds)

    except:
        print("NRL unsuccessful")
        return render_template('login.html') # Or redirect(url_for('login'))

    
    

    
    
@app.route("/dashboard")
def dashboard():
 return "<h1>Welcome!</h1>"

# Initialize Firebase Admin SDK (replace with your service account file)
# Keep this file secure and do not commit it to your code repository.


@app.route('/verify-token', methods=['POST'])
def verify_token():
    id_token = request.json.get('idToken')
    #print (id_token)
    try:
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        print("success")
        return jsonify({'message': 'Authenticated successfully', 'uid': uid})
    except Exception as e:
        print ("error 1")
        return jsonify({'error': str(e)}), 401

@app.route('/protected-resource')
def protected_resource():
    # Get the ID token from the Authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Authorization header missing'}), 401

    id_token = auth_header.split(' ')[1] if len(auth_header.split(' ')) > 1 else None
    if not id_token:
        return jsonify({'error': 'Bearer token not found'}), 401

    try:
        # Verify the ID token
        decoded_token = auth.verify_id_token(id_token)
        # Token is valid, user is authenticated
        return 'This is a protected resource!'
    except Exception as e:
        # Token is invalid
        return jsonify({'error': str(e)}), 401




# Replace with your actual API key and the correct endpoint
# Remember to handle your API key securely and avoid committing it directly into your code.
API_KEY = "1a165e5a772d74d1fd607c052cabb72a"
API_ENDPOINT = "https://api.the-odds-api.com/v4/sports/rugbyleague_nrl/odds" # Example endpoint

def get_nrl_odds(api_key, api_endpoint):
  """Fetches NRL rugby odds from OddsAPI."""
  try:
    response = requests.get(api_endpoint, params={
        'api_key': api_key,
        'regions': 'au',  # Example: Get odds from Australian bookmakers
        'markets': 'h2h', # Example: Get head-to-head odds
        'oddsFormat': 'decimal', # Example: Get odds in decimal format
    })
    response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
    data = response.json()

    return data
  except requests.exceptions.RequestException as e:
    print(f"Error fetching data from OddsAPI: {e}")
    return None

def main():
    app.run(port=int(os.environ.get('PORT', 5000)))

if __name__ == "__main__":
    
    main()
