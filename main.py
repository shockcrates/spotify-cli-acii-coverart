import requests
import os
import base64
from token_handler import get_token


def request_artist_data():
    access_token = get_token()
    base_url = "https://api.spotify.com/v1/artists/4Z8W4fKeB5YxbusRsdQVPb"
    header = {"Authorization": f"Bearer {access_token}"}

    x = requests.get(url=base_url, headers=header)

    print(f"STATUS: {x.status_code}")
    if x.ok != True:
        print("THINGS ARE NOT OK")
        return 
    print(f"Name: {x.json()["name"]}")


def main():
    #request_access_token()
    request_artist_data()


if __name__ == "__main__":
    main()


"""
1. Initialize and say hi to user
2. Ask for sign in or check for existing saved valid credentials
3. Connect to spotify and request intial info
4. List out available playlists, maybe show last played
5. Song Selection:
    - Start from 1st song right away? - start here for simplicity
    - Show list of available and make user select first song?
    - Start with a random song?
    - Can I implement autocomplete when searching for a song?  - Yes use prompt toolkit and word completer

"""