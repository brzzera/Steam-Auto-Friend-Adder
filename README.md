# Steam Auto Friend Adder

A **Python** script to automate sending friend requests on Steam from members of a specific group.

---

## 🚀 What it does

- Scrapes the first members of a public Steam group.
- Checks if each member’s **SteamID64** is in the correct format.
- Asks the user whether to send a friend request to that profile.
- Sends the friend request via **POST** request using valid Steam session cookies.
- Pauses between requests to avoid **flood restrictions**.

---

## ⚙️ Requirements

- **Python 3.7+**
- Libraries: `requests`, `beautifulsoup4`
- Valid Steam session cookies: `steamLoginSecure` and `sessionid` for authentication

---

## 🛠 How to use

1. Insert your valid Steam cookies in the `COOKIES` dictionary inside the script.
2. Change the group URL in the `GROUP_URL` variable to the Steam group you want to scrape.
3. Run the script:
   ```bash
   python add_friends.py
   ```
4. For each user found, the script will ask:
   ```
   [?] Add https://steamcommunity.com/profiles/STEAMID64? (y/n)
   ```
   Reply **`y`** to send a friend request or **`n`** to skip.

---

## 🔍 How to find SteamIDs64

- Go to any Steam user’s profile.
- If the URL looks like this:
  
  `https://steamcommunity.com/profiles/76561198012345678`
  
  then `76561198012345678` is their **SteamID64**.

- If the URL is a custom URL like:
  
  `https://steamcommunity.com/id/customname/`
  
  you can convert it to SteamID64 by using tools such as:

  - [SteamID Finder](https://steamidfinder.com/)
  - [SteamRep](https://steamrep.com/)
  
  Just paste the custom URL or username and get the corresponding SteamID64.

---

## ⚠️ Warning

- Using this script **may violate Steam’s Terms of Service**. Use responsibly and at your own risk.
- The script **does not check if you are already friends or if a request was already sent**.
- It's recommended to have delays between requests (default 2 seconds) to avoid **temporary bans**.

---

If you want me to help you add **installation instructions**, **example outputs**, or anything else, just ask!

> By: brzera
