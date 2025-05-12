import time
import json
import os
import base64
import random
import hashlib
from dotenv import load_dotenv
from requests import post, Response, get
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse

"""
1. Generate PKCE pair - done
2. Start temporary local HTTP server to catch the redirect with the auth code - written
3. Open the browser to the authorization url - written
4. wait for code on the redirect - written
5. Exchange code for the token
"""

load_dotenv()
client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = "http://127.0.0.1:8080/callback" #maybe change to http, also in app on website
AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL= "https://accounts.spotify.com/api/token"
scope = "user-read-private user-top-read user-read-email playlist-read-private playlist-read-collaborative"
TOKEN_FILE = "token.json"
TIME_LIMIT_SEC = 3600

def generate_random_string(size):
    available = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-~"
    indexes = [random.randint(0,len(available)-1) for _ in range(size)]
    rand_string = "".join([available[indexes[i]] for i in range(size)])
    return rand_string

def generate_pkce_pair(size):
    rand_string = generate_random_string(size)
    code_verfier = base64.urlsafe_b64encode(rand_string.encode()).decode('utf-8').rstrip("=")
    challenge_bytes = hashlib.sha256(code_verfier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(challenge_bytes).decode('utf-8').rstrip("=")
    return code_verfier, code_challenge


class AuthHandler(BaseHTTPRequestHandler):
    auth_code = None

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if (parsed.path == "/callback"):
            queries = urllib.parse.parse_qs(parsed.query)
            AuthHandler.auth_code = queries.get('code',[None][0])
            self.send_response("200")
            self.end_headers()
            self.wfile.write("<h1>Auth done. Geeeeeeet out of here.</h1")

        else:
            self.send_error(404)


def start_server():
    server = HTTPServer(("localhost",8080), AuthHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    return server

def get_access_token():
    code_verifier, code_challenge = generate_pkce_pair(64)
    data = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": scope,
        "code_challenge_method": "S256",
        "code_challenge": code_challenge
    }

    authentication_request_url = f"{AUTH_URL}?{urllib.parse.urlencode(data)}"

    try:
        server = start_server()

        print("Opening Browser to spotify for login")
        webbrowser.open(authentication_request_url)

        #wait for redirect and data read to happen

        timeout_limit = 120
        start_time = time.time()
        while(AuthHandler.auth_code == None):
            if time.time() - start_time > timeout_limit:
                print("Timed out")
                break
            time.sleep(0.1)
            

        print(f"Authentication code received: {AuthHandler.auth_code}")
    
        

        data2 = {
            "grant_type": "authorization_code",
            "code": AuthHandler.auth_code,
            "redirect_uri": REDIRECT_URI,
            "client_id": client_id,
            "code_verifier": code_verifier
        }
        header = {
            "Conetent-Type": "application/x-www-form-urlencoded"
        }

        answer = post(url=TOKEN_URL, headers=header, data=data2)

        if answer.ok != True:
            print("POST has failed")
            raise ValueError
        else:
            print("Successfully got access token!!")
        
        return answer.json()["access_token"], answer.json()
    finally:
        print("Shutting down server")
        server.shutdown()


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

def save_token(token_response_json):
    if os.path.exists(TOKEN_FILE):              #to handle if a new refresh token isnt given
        if token_response_json["refresh_token"] == None:
            with open(TOKEN_FILE, "r") as openf:
                token_data = json.load(openf)
                old_ref_tok = token_data["refresh_token"]
            with open(TOKEN_FILE, "w") as openf:
                json.dump({"access_token":token_response_json["access_token"],
                        "refresh_token": old_ref_tok,
                        "scope": token_response_json["scope"],
                        "timestamp": time.time()}
                        , openf)
            return 
    with open(TOKEN_FILE, "w") as openf:
        json.dump({"access_token":token_response_json["access_token"],
                "refresh_token": token_response_json["refresh_token"],
                "scope": token_response_json["scope"],
                "timestamp": time.time()}
                , openf)
            

def refresh_token():
    with open(TOKEN_FILE) as fopen:
        token_data = json.load(fopen)
    
    ref_token = token_data["refresh_token"]

    data = {
        "grant_type": "refresh_token",
        "refresh_token": ref_token,
        "client_id": client_id
    }

    header = {
        "Content-Type": "application/x-www-form-urlencoded",
    }

    answer = post(url=TOKEN_URL, headers=header, data=data)

    if answer.ok != True:
        print("Refresh did not go as planned")
        raise ValueError
    return answer.json()["access_token"], answer.json()

def create_or_refresh_token():
    if not os.path.exists(TOKEN_FILE):
        token, response_json = get_access_token()
        save_token(response_json)
        return token
    #Must need refresh assuming no one messes with the json file
    token, response_json = refresh_token()
    save_token(response_json)
    return token

def get_token():
    try:
        if is_valid_token():
            return get_saved_token()
        else:
            token = create_or_refresh_token()
            return token
    except ValueError:
        print("No Luck. Try again")




    