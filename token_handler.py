import time
import json
import os
import base64
from dotenv import load_dotenv
from requests import post, Response

load_dotenv()
client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

TOKEN_FILE = "token.json"
TIME_LIMIT_SEC = 3600

def request_access_token():
    '''
    curl -X POST "https://accounts.spotify.com/api/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "grant_type=client_credentials&client_id=your-client-id&client_secret=your-client-secret"    
    '''
    auth_str = f"{client_id}:{client_secret}"
    b64_str = base64.b64encode(auth_str.encode()).decode()
    url = "https://accounts.spotify.com/api/token"
    headers = {"Authorization":f"Basic {b64_str}"}
    data = {"grant_type": "client_credentials"}
    
    x = post(url=url, headers=headers, data=data)
    print(f"Status: {x.status_code}")
    
    if (x.status_code > 300):
        raise ValueError
   
    
    print(f"ACCESS_TOKEN: {x.json()["access_token"]}")
    return x.json()["access_token"]

def is_valid_token():
    if not os.path.exists(TOKEN_FILE):
        return False
    
    with open(TOKEN_FILE) as fopen:
        token_data = json.load(fopen)
    
    return time.time() - token_data["timestamp"] < TIME_LIMIT_SEC
    

def get_saved_token():
    with open(TOKEN_FILE) as openf:
        Token = json.load(openf)["access_token"]
    return Token


def save_token(token):
    with open(TOKEN_FILE, "w") as openf:
        json.dump({"access_token":token,
                   "timestamp": time.time()}
                   , openf)
        
def get_token():
    try:
        if is_valid_token():
            return get_saved_token()
        else:
            token = request_access_token()
            save_token(token)
            return token
    except ValueError:
        print("No Luck. Try again")