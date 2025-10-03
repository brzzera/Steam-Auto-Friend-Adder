import requests
from bs4 import BeautifulSoup
import time

# ==========================
# CONFIGURATION
# ==========================

# Your Steam cookies
COOKIES = {
    'steamLoginSecure': 'PASTE_YOUR_COOKIE_HERE',
    'sessionid': 'PASTE_YOUR_COOKIE_HERE'
}

# Your Steam Web API Key
STEAM_API_KEY = "PASTE_YOUR_API_KEY_HERE"

# Target Steam Group URL
GROUP_URL = 'https://steamcommunity.com/groups/YOUR_GROUP/members'

# Max members to fetch
MAX_USERS = 50

# Mode: True = automatic (no prompt), False = interactive
AUTO_MODE = False

# Delay between requests (seconds)
REQUEST_DELAY = 2

# ==========================
# FUNCTIONS
# ==========================

def vanity_to_steamid64(vanity_url):
    """Convert vanity URL to SteamID64 using Steam Web API"""
    url = f"https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/?key={STEAM_API_KEY}&vanityurl={vanity_url}"
    response = requests.get(url)
    data = response.json()
    if data['response']['success'] == 1:
        return data['response']['steamid']
    else:
        print(f"[-] Could not convert vanity URL: {vanity_url}")
        return None

def get_steam_ids(group_url, max_users=50):
    """Fetch first members from the Steam group"""
    print(f"[+] Fetching the first {max_users} members from the group...")
    response = requests.get(group_url, headers={'User-Agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(response.text, 'html.parser')
    users = soup.select('.member_block .linkFriend')
    steam_ids = [user['href'].split('/')[-1] for user in users][:max_users]
    return steam_ids

def add_friend(steam_id64):
    """Send friend request to SteamID64"""
    profile_url = f'https://steamcommunity.com/profiles/{steam_id64}'
    
    if not AUTO_MODE:
        confirm = input(f"[?] Add {profile_url}? (y/n)\n> ").lower()
        if confirm != 'y':
            return
    
    friend_url = "https://steamcommunity.com/actions/AddFriendAjax"
    payload = {
        'sessionID': COOKIES['sessionid'],
        'steamid': steam_id64
    }
    try:
        r = requests.post(friend_url, headers={'User-Agent': 'Mozilla/5.0'}, cookies=COOKIES, data=payload)
        if r.status_code == 200:
            print(f"[✔] Friend request sent to {steam_id64}")
        else:
            print(f"[x] Error adding {steam_id64}: HTTP {r.status_code}")
    except Exception as e:
        print(f"[!] Error: {e}")

# ==========================
# MAIN
# ==========================

def main():
    steam_ids = get_steam_ids(GROUP_URL, MAX_USERS)
    
    for sid in steam_ids:
        if sid.isdigit() and len(sid) == 17:
            add_friend(sid)
        else:
            steamid = vanity_to_steamid64(sid)
            if steamid:
                add_friend(steamid)
        time.sleep(REQUEST_DELAY)

if __name__ == "__main__":
    main()
