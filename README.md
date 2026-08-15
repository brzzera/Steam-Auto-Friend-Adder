# 🚀 Steam Auto Friend Adder v3.0

**Author:** brzera
**Language:** Python
**Platform:** Windows / Linux / macOS

---

## Overview

**Steam Auto Friend Adder v2.0** is a Python tool for managing and sending Steam friend requests to members of public Steam groups.

Version 2.0 introduces a complete terminal interface, saved Steam accounts, secure credential storage, group member detection, pending invite management, SteamID64/Vanity URL support, and protection against Steam rate limits.

Instead of manually editing cookies and API keys inside the source code, accounts can now be added and loaded directly from the program.

---

## ✨ Features

* 👤 **Multiple Steam accounts**

  * Save multiple Steam logins.
  * Select an account from the main menu.
  * Delete saved accounts.

* 🔐 **Secure credential storage**

  * `steamLoginSecure`
  * `sessionid`
  * Steam Web API Key
  * Credentials are stored using the operating system's **Keyring**, not directly inside the JSON configuration file.

* 👥 **Steam Group Member Fetching**

  * Fetch members from public Steam groups.
  * Supports URLs such as:

    ```text
    https://steamcommunity.com/groups/example
    ```

    or:

    ```text
    https://steamcommunity.com/groups/example/members
    ```

* 🔎 **SteamID64 Detection**

  * Reads Steam profile information from the group members page.
  * Supports SteamID64 profiles.
  * Supports custom Vanity URLs.
  * Automatically converts Vanity URLs using the Steam Web API.

* 📋 **Member Preview**

  * Shows the members found before sending requests.
  * Displays:

    * Steam username
    * Steam profile URL
    * SteamID64 when necessary

* ➕ **Friend Request Automation**

  * Interactive mode to confirm every friend request.
  * Optional automatic mode.
  * Tracks requests sent by the program.

* ⏳ **Request Delay**

  * Configurable delay between Steam requests.
  * Helps reduce the chance of triggering Steam flood/rate protection.

* 📨 **Pending Invite Detection**

  * Attempts to read outgoing friend requests directly from Steam's pending friends page.
  * Displays pending Steam accounts and profile URLs.
  * Keeps a local history as a fallback.

* ❌ **Remove Pending Invites**

  * Remove one outgoing pending friend request.
  * Remove all detected outgoing pending requests.

* 🛡️ **Rate Limit Handling**

  * Detects HTTP `429 Too Many Requests`.
  * Stops repeated requests when Steam applies rate limiting.
  * Uses the normal Steam group members page as the primary source.
  * Includes the legacy group XML endpoint as a secondary fallback.

* 🖥️ **Clean Terminal Interface**

  * Clears the terminal between actions.
  * Prevents the menu from being duplicated continuously.
  * Works with both Windows (`cls`) and Unix systems (`clear`).

---

## 📋 Main Menu

When the program starts:

```text
=================================================
              STEAM AUTO FRIEND
=================================================
Logged account: NONE

1 - Login Account
2 - Add Login
3 - Auto Add Friends
4 - Remove Pending Invites
5 - View Pending Invites
6 - Delete Login
0 - Exit

>
```

---

## Requirements

### Python

Python **3.7+** is recommended.

Check your version:

```bash
python --version
```

or:

```bash
python3 --version
```

### Python Libraries

Install the required dependencies:

```bash
pip install requests beautifulsoup4 keyring
```

The script uses:

* `requests`
* `beautifulsoup4`
* `keyring`

The remaining modules are included with Python.

---

## 🔑 Steam Web API Key

The Steam Web API Key is used for:

* Resolving Vanity URLs.
* Retrieving Steam usernames.
* Retrieving Steam profile URLs.

### Getting an API Key

1. Log in to Steam.

2. Open:

   https://steamcommunity.com/dev/apikey

3. Register a Web API Key.

4. For personal usage, you can normally use:

   ```text
   localhost
   ```

   as the domain.

5. Copy the generated API Key.

You will enter it when creating an account inside the program.

You **do not need to paste the API Key directly into the Python source code**.

---

## 🍪 Getting Steam Session Cookies

Steam authentication requires:

```text
steamLoginSecure
sessionid
```

### Chrome / Chromium

1. Log in to:

   https://steamcommunity.com/

2. Press:

   ```text
   F12
   ```

3. Open:

   ```text
   Application
   ```

4. Go to:

   ```text
   Storage
   └── Cookies
       └── https://steamcommunity.com
   ```

5. Find:

   ```text
   steamLoginSecure
   ```

   and:

   ```text
   sessionid
   ```

6. Copy their values.

---

## ⚠️ Important Security Warning

Your `steamLoginSecure` cookie is sensitive authentication data.

**Never:**

* Share it with another person.
* Post it on GitHub.
* Put it inside screenshots.
* Send it through Discord.
* Commit it to a public repository.

The program uses Python's `keyring` package so these credentials do not need to be stored directly inside the Python source code.

The local JSON database stores account aliases and local request history, but not the Steam login cookies themselves.

---

## 👤 Adding an Account

Start the program:

```bash
python steam_auto_friend_v2.py
```

Select:

```text
2 - Add Login
```

Example:

```text
--- ADD LOGIN ---

Account name / alias: TheBigRooster

Paste the Steam credentials.
They will not be shown while typing.

steamLoginSecure:
sessionid:
Steam Web API Key:
```

After entering the credentials:

```text
[+] Account 'TheBigRooster' saved.
```

The credential fields are hidden while typing.

---

## 🔓 Loading a Saved Account

Select:

```text
1 - Login Account
```

Example:

```text
--- LOGIN ACCOUNT ---

1 - TheBigRooster
2 - AltAccount
0 - Cancel

> 1
```

The program checks whether the saved Steam session is still valid.

If successful:

```text
[+] Logged into saved profile: TheBigRooster
```

If the cookies expired:

```text
[x] steamLoginSecure/sessionid is invalid or expired.
```

In that case, obtain new Steam cookies and add/update the login again.

---

## 👥 Auto Add Friends

Select:

```text
3 - Auto Add Friends
```

Enter your Steam group:

```text
Group URL:
https://steamcommunity.com/groups/revbr
```

You may also use:

```text
https://steamcommunity.com/groups/revbr/members
```

Then choose the maximum number of users:

```text
Max users [50]: 5
```

The program will retrieve the first group members:

```text
[+] Loading first 5 members...
[+] Found 5 members:

  1. ExampleUser
     https://steamcommunity.com/id/example

  2. AnotherUser
     https://steamcommunity.com/profiles/76561198XXXXXXXXX
```

Before sending anything:

```text
Start sending requests? (y/n):
```

---

## 🎮 Interactive Mode

By default:

```python
AUTO_MODE = False
```

The program asks before each request:

```text
[1/5] ExampleUser

Add https://steamcommunity.com/id/example? (y/n/q):
```

Options:

```text
y = send request
n = skip user
q = stop the operation
```

---

## ⚡ Automatic Mode

To automatically process the loaded group members, change:

```python
AUTO_MODE = True
```

The individual confirmation prompt will be skipped.

Use automatic mode carefully.

---

## 📨 Pending Friend Invites

Select:

```text
5 - View Pending Invites
```

The program attempts to read outgoing pending friend requests from:

```text
https://steamcommunity.com/my/friends/pending
```

Example:

```text
--- SENT PENDING INVITES ---

  1. ExampleUser
     https://steamcommunity.com/id/example
     SteamID64: 76561198XXXXXXXXX

  2. AnotherUser
     https://steamcommunity.com/profiles/76561198XXXXXXXXX
     SteamID64: 76561198XXXXXXXXX

Total: 2
```

---

## 🗃️ Local Pending History

Every successful friend request sent through the program is also recorded locally.

The JSON database looks similar to:

```json
{
    "accounts": {
        "TheBigRooster": {
            "tracked_sent": [
                "76561198XXXXXXXXX",
                "76561198XXXXXXXXX"
            ]
        }
    }
}
```

This is used as a fallback if Steam changes the HTML structure of its pending invite page.

A locally tracked request may already have been:

* Accepted.
* Declined.
* Cancelled outside the script.

For this reason, live Steam data is preferred whenever it can be detected correctly.

---

## ❌ Removing Pending Friend Invites

Select:

```text
4 - Remove Pending Invites
```

Example:

```text
--- REMOVE SENT PENDING INVITES ---

  1. ExampleUser
     https://steamcommunity.com/id/example

  2. AnotherUser
     https://steamcommunity.com/profiles/76561198XXXXXXXXX

A - Remove ALL
0 - Cancel

Select number or A:
```

Enter a number to remove one request:

```text
> 1
```

Or:

```text
> A
```

to cancel all detected outgoing pending requests.

---

## 🌐 Group Member Detection

Steam Auto Friend Adder v2.0 uses multiple methods for finding group members.

### Primary Method

The public group members page:

```text
https://steamcommunity.com/groups/GROUP_NAME/members
```

The program extracts Steam account information from the HTML and converts it to SteamID64.

### XML Fallback

If HTML detection fails, the program can attempt Steam's group XML endpoint:

```text
/memberslistxml/?xml=1
```

This endpoint may be rate-limited more aggressively by Steam, so it is only used as a fallback.

---

## 🚫 HTTP 429 / Steam Rate Limiting

Steam may respond with:

```text
HTTP 429 Too Many Requests
```

Example:

```text
[x] Steam rate-limited the group members page (HTTP 429).
Avoid repeated retries and try again later.
```

This means Steam temporarily limited requests from your connection.

Do **not** repeatedly restart the script or continuously retry while receiving HTTP 429 responses.

The script intentionally stops instead of continuously sending more requests.

---

## ⚙️ Configuration

Important configuration values are near the top of the script:

```python
DEFAULT_GROUP_URL = "https://steamcommunity.com/groups/Fnatic"

MAX_USERS = 50

AUTO_MODE = False

REQUEST_DELAY = 2
```

### `DEFAULT_GROUP_URL`

Default Steam group:

```python
DEFAULT_GROUP_URL = "https://steamcommunity.com/groups/Fnatic"
```

### `MAX_USERS`

Default maximum members:

```python
MAX_USERS = 50
```

### `AUTO_MODE`

Interactive:

```python
AUTO_MODE = False
```

Automatic:

```python
AUTO_MODE = True
```

### `REQUEST_DELAY`

Delay between friend operations:

```python
REQUEST_DELAY = 2
```

---

## 🗑️ Deleting Saved Accounts

Select:

```text
6 - Delete Login
```

Select the saved account and confirm:

```text
Delete 'TheBigRooster'? (y/n):
```

Deleting an account removes:

* Its saved Steam credentials from the Keyring.
* Its entry from the local account database.
* Its locally tracked friend request history.

---

## 📁 Files

The project can contain:

```text
SteamAutoFriend/
│
├── steam_auto_friend_v2.py
├── steam_accounts.json
└── README.md
```

`steam_accounts.json` is automatically generated after adding an account.

---

## 🧠 How It Works

Simplified flow:

```text
Steam Group URL
      │
      ▼
Public Members Page
      │
      ▼
Extract Accounts
      │
      ▼
SteamID64
      │
      ▼
Steam Web API
      │
      ├── Username
      └── Profile URL
      │
      ▼
Display Members
      │
      ▼
User Confirmation
      │
      ▼
Friend Request
      │
      ▼
Local Tracking
```

---

## ⚠️ Notes & Warnings

* Steam may change its website structure at any time.
* Internal Steam Community endpoints can change without notice.
* Friend request automation may trigger Steam spam/flood protection.
* Steam may temporarily rate-limit requests.
* Large automated batches are not recommended.
* Start with a very small `MAX_USERS` value when testing.
* Do not attempt to bypass Steam rate limits.
* Protect your Steam authentication cookies and API Key.
* You are responsible for how you use this program and for complying with Steam's rules.

---

## Example Configuration

For manual confirmation:

```python
DEFAULT_GROUP_URL = "https://steamcommunity.com/groups/revbr"
MAX_USERS = 10
AUTO_MODE = False
REQUEST_DELAY = 2
```

For automatic mode:

```python
DEFAULT_GROUP_URL = "https://steamcommunity.com/groups/revbr"
MAX_USERS = 20
AUTO_MODE = True
REQUEST_DELAY = 2
```

---

## Changelog — v3.0

### Added

* Multi-account support.
* Saved login profiles.
* Secure Keyring credential storage.
* Login session validation.
* Clean terminal UI.
* Automatic terminal clearing.
* Steam group HTML member parser.
* XML fallback.
* Vanity URL conversion.
* SteamID64 detection.
* Player name/profile lookup.
* Member preview.
* Friend request tracking.
* Live pending invite detection.
* Local pending invite fallback.
* Remove individual pending invites.
* Remove all pending invites.
* HTTP 429 rate-limit handling.
* Cross-platform terminal support.

### Changed

* Credentials no longer need to be hardcoded inside the script.
* HTML group member detection is now preferred over Steam's XML endpoint.
* Pending friend requests are no longer based exclusively on locally saved IDs.

---

## Disclaimer

This project is an unofficial community tool and is **not affiliated with, endorsed by, or supported by Valve Corporation or Steam**.

Steam, the Steam logo, and related trademarks belong to Valve Corporation.

Use this software responsibly and at your own risk.

---

# 🚀 Steam Auto Friend Adder v3.0

**Created by brzera**
