import os
import requests

import firebase_admin
from firebase_admin import credentials
from firebase_admin import auth
from firebase_admin import exceptions
from firebase_admin import firestore
import google.cloud.secretmanager as secretmanager

import json, google.oauth2.service_account
from flask import Flask, send_file, jsonify, render_template, request, session
from flask import redirect, url_for
app = Flask(__name__)

app.config['SECRET_KEY'] = 'a_very_secret_key_for_session_management'

combined_teams_odds =[]
uid = None
@app.route("/")
def index():

    ### Enable this for test
    cred = credentials.Certificate('src/serviceAccountKey.json') # <-- REPLACE WITH YOUR SERVICE ACCOUNT FILE PATH
    #cred = credentials.Certificate() # <-- REPLACE WITH YOUR SERVICE ACCOUNT FILE PATH

    
    # print(cred)
    project_id = "box-dout" # os.environ.get("boxdout")
    print("this is project ID: ", project_id)
    secret_name = "serviceAccKey" # Replace with the name of your secret in Secret Manager
    version_id = "1"

    def access_secret_version(project_id, secret_name, version_id):
        """
        Access the payload for the given secret version if one exists. The version
        can be a version number as a string (e.g. "5") or an alias (e.g. "latest").
        """
        client = secretmanager.SecretManagerServiceClient()

        name = "projects/736778846282/secrets/serviceAccKey/versions/1"

        response = client.access_secret_version(request={"name": name})

        payload = response.payload.data.decode("UTF-8")
        print(payload)
        return payload

    try:
        #### Enable this for Prod. Retrieve the service account key from Secret Manager
        # service_account_key_json = access_secret_version(project_id, secret_name, version_id)
        # #cred = google.oauth2.service_account.Credentials.from_service_account_info(json.loads(service_account_key_json))
        # cred = credentials.Certificate(json.loads(service_account_key_json)) # <-- REPLACE WITH YOUR SERVICE ACCOUNT FILE PATH

        firebase_admin.initialize_app(cred)
        print("firebase initialized")
    except (exceptions.FirebaseError, Exception) as e:
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
    username = None
    try:
        # Assuming the user is authenticated and their UID is available
        # You would typically get the UID from a session or request header
        # For demonstration, let's assume a UID is available (you'll need to adapt this)
        # For example, if you store the UID in the session after login:
        # uid = session.get('user_id')

        # **IMPORTANT:** Replace the following line with how you actually get the authenticated user's UID
        # For this example, I'll use a placeholder UID. You need to get the real UID of the logged-in user.
        # You might get this from the verified ID token in a real application.
        uid = session.get('user_id') # Replace with actual UID retrieval

        db = firestore.client()
        print(uid)
        user_ref = db.collection('users').document(uid)
        user_doc = user_ref.get()
        print(user_doc)
        if user_doc.exists:
            user_data = user_doc.to_dict()
            username = user_data.get('username')
            print(username)
        else: 
            print("no user")
    except Exception as e:
        print(f"Error fetching user data: {e}")
        username = "Guest" # Default name if fetching fails

    return render_template('homepage.html', username=username)

@app.route("/wallet_page")
def wallet_page():
        uid = session.get('user_id')
        if not uid:
            return redirect(url_for('login'))

        db = firestore.client()
        user_ref = db.collection('users').document(uid)
        user_doc = user_ref.get()
        balance = 0.0
        if user_doc.exists:
            balance = user_doc.to_dict().get('balance', 0.0)
        return render_template('wallet.html', balance=balance)
@app.route("/deposit", methods=['POST'])
def deposit():
    uid = session.get('user_id')
    if not uid:
        return jsonify({'error': 'User not authenticated'}), 401

    amount = request.form.get('amount', type=float)
    if amount is None or amount <= 0:
        return jsonify({'error': 'Invalid deposit amount'}), 400

    db = firestore.client()
    user_ref = db.collection('users').document(uid)

    try:
        user_doc = user_ref.get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            current_balance = user_data.get('balance', 0.0)
            new_balance = current_balance + amount
            user_ref.update({'balance': new_balance})
            return redirect(url_for('wallet_page'))
        else:
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        print(f"Error depositing funds: {e}")
        return jsonify({'error': 'Failed to process deposit'}), 500

@app.route("/withdraw", methods=['POST'])
def withdraw():
    uid = session.get('user_id')
    if not uid:
        return jsonify({'error': 'User not authenticated'}), 401

    amount = request.form.get('amount', type=float)
    if amount is None or amount <= 0:
        return jsonify({'error': 'Invalid withdrawal amount'}), 400

    db = firestore.client()
    user_ref = db.collection('users').document(uid)

    try:
        user_doc = user_ref.get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            current_balance = user_data.get('balance', 0.0)

            if current_balance < amount:
                return jsonify({'error': 'Insufficient funds'}), 400

            new_balance = current_balance - amount
            user_ref.update({'balance': new_balance})
            return redirect(url_for('wallet_page'))
        else:
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        print(f"Error withdrawing funds: {e}")
        return jsonify({'error': 'Failed to process withdrawal'}), 500




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
    print (id_token)
    try:
        decoded_token = firebase_admin.auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        session['user_id'] = uid

        print("success")
        return jsonify({'message': 'Authenticated successfully', 'uid': uid})
    except Exception as e:
        print ("error 1",e)
        
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
API_KEY = os.environ.get('MY_API_KEY')
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
