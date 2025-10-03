# 🚀 Steam Auto Friend Adder v2.0

**Author:** brzera
**Language:** Python

---

## Overview

**Steam Auto Friend Adder v2.0** is a Python script that automates sending friend requests to members of a specified Steam group.
This version supports both **SteamID64** and **Vanity URLs**, automatically converting Vanity URLs to SteamID64 using the Steam Web API.

---

## Features

* Fetches the first members from any **public Steam group**.
* Supports **Vanity URLs** (custom profile names) and converts them to SteamID64.
* Interactive mode to confirm each friend request.
* Optional automatic mode to send requests to all members without prompts.
* Delay between requests to reduce the risk of triggering Steam flood protection.
* Uses **Steam session cookies** (`steamLoginSecure` and `sessionid`) for authentication.

---

## Requirements

* Python 3.7 or higher
* `requests` and `beautifulsoup4` libraries:

  ```bash
  pip install requests beautifulsoup4
  ```
* A **Steam account** (not limited)
* Steam **session cookies** (`steamLoginSecure` and `sessionid`)
* Steam **Web API Key**

---

## Getting Your Steam Web API Key

1. Log in to your Steam account.
2. Go to [https://steamcommunity.com/dev/apikey](https://steamcommunity.com/dev/apikey)
3. Fill in the **Domain Name** (use `localhost` for personal scripts).
4. Click **“I agree – Register”**.
5. Copy the API Key provided.
6. Paste it in the script under:

   ```python
   STEAM_API_KEY = "YOUR_API_KEY_HERE"
   ```

---

## Getting Your Steam Session Cookies

1. Log in to [Steam](https://steamcommunity.com/) in your browser.
2. Press `F12` → **Application** → **Cookies**.
3. Copy:

   * `steamLoginSecure`
   * `sessionid`
4. Paste them in the script:

   ```python
   COOKIES = {
       'steamLoginSecure': 'PASTE_HERE',
       'sessionid': 'PASTE_HERE'
   }
   ```

> ⚠️ Keep your cookies private. Do not share them.

---

## Usage

1. Update your **Steam cookies** and **API Key** in the script.
2. Set your **target Steam group URL**:

   ```python
   GROUP_URL = 'https://steamcommunity.com/groups/YOUR_GROUP/members'
   ```
3. Set `MAX_USERS` to the number of members you want to add.
4. Choose mode:

   * `AUTO_MODE = False` → interactive (confirm each friend request)
   * `AUTO_MODE = True` → automatically add all members
5. Run the script:

   ```bash
   python steam_auto_friend_adder.py
   ```

---

## Notes & Warnings

* The script **does not check** if the friend request was already sent.
* Automating friend requests may violate Steam’s **Terms of Service**. Use responsibly.
* Keep a **delay between requests** (`time.sleep(2)`) to avoid flood protection.
* Start with a small number of friends to test.

---

## Example

```python
# Interactive mode example
AUTO_MODE = False
MAX_USERS = 20
GROUP_URL = 'https://steamcommunity.com/groups/the_wired/members'
```

```python
# Automatic mode example
AUTO_MODE = True
MAX_USERS = 50
GROUP_URL = 'https://steamcommunity.com/groups/the_wired/members'
```

---

**Enjoy your new Steam Auto Friend Adder v2.0! 🚀**
Created by brzera
