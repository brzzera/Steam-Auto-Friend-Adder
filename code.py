import requests
from bs4 import BeautifulSoup
import time

# ==== INSERT YOUR COOKIES HERE ====
COOKIES = {
    'steamLoginSecure': 'LoginSecureID',
    'sessionid': 'SessionID'
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0'
}

# Group URL
GROUP_URL = 'https://steamcommunity.com/groups/YOUR_GROUP_NAME_HERE/members'

def get_steam_ids(group_url, max_users=50):
    print(f"[+] Fetching the first {max_users} members from the group...")
    response = requests.get(group_url, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')
    users = soup.select('.member_block .linkFriend')
    steam_ids = [user['href'].split('/')[-1] for user in users][:max_users]
    return steam_ids

def add_friend(steam_id64):
    profile_url = f'https://steamcommunity.com/profiles/{steam_id64}'
    confirm = input(f"[?] Add {profile_url}? (y/n)\n> ").lower()
    if confirm != 'y':
        return
    friend_url = "https://steamcommunity.com/actions/AddFriendAjax"
    payload = {
        'sessionID': COOKIES['sessionid'],
        'steamid': steam_id64
    }
    try:
        r = requests.post(friend_url, headers=HEADERS, cookies=COOKIES, data=payload)
        if r.status_code == 200:
            print(f"[✔] Friend request sent to {steam_id64}")
        else:
            print(f"[x] Error adding {steam_id64}: HTTP {r.status_code}")
    except Exception as e:
        print(f"[!] Error: {e}")

def main():
    steam_ids = get_steam_ids(GROUP_URL)
    for sid in steam_ids:
        if sid.isdigit():
            add_friend(sid)
        else:
            print(f"[-] Skipped: {sid} is not a SteamID64.")
        time.sleep(2)  # Pause between requests to avoid flood

if __name__ == "__main__":
    main()
