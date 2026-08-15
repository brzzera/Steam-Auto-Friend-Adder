"""
Steam Auto Friend Adder v3.0
Author: brzera

Public release:
- No Steam cookies, API keys, account names, SteamIDs, or private group URLs are hardcoded.
- Credentials are entered locally by the user and stored through the OS keyring.
- Use responsibly and comply with Steam rules and rate limits.
"""

import getpass
import json
import os
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

import keyring
import requests
from bs4 import BeautifulSoup
from keyring.errors import PasswordDeleteError


# ============================================================
# CONFIG
# ============================================================

DB_FILE = Path(__file__).with_name("steam_accounts.json")
KEYRING_SERVICE = "steam-auto-friend"

DEFAULT_GROUP_URL = ""
MAX_USERS = 50
AUTO_MODE = False
REQUEST_DELAY = 2

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/151.0.0.0 Safari/537.36"
)


# ============================================================
# UI
# ============================================================

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def pause(message="Press ENTER to return to menu..."):
    input(f"\n{message}")


def header(current_account=None):
    print("=" * 49)
    print("          STEAM AUTO FRIEND ADDER v3.0")
    print("=" * 49)
    print(f"Logged account: {current_account or 'NONE'}")
    print()


def action_screen(title, current_account=None):
    clear_screen()
    header(current_account)
    print(f"--- {title} ---\n")


# ============================================================
# DATABASE
# ============================================================

def load_db():
    if not DB_FILE.exists():
        return {"accounts": {}}

    try:
        with DB_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("accounts", {})
        for info in data["accounts"].values():
            if "tracked_sent" not in info:
                info["tracked_sent"] = info.pop("pending_sent", [])
        return data
    except (json.JSONDecodeError, OSError):
        return {"accounts": {}}


def save_db(db):
    with DB_FILE.open("w", encoding="utf-8") as f:
        json.dump(db, f, indent=4, ensure_ascii=False)


# ============================================================
# KEYRING / SECRETS
# ============================================================

def save_secret(account_name, key, value):
    keyring.set_password(KEYRING_SERVICE, f"{account_name}:{key}", value)


def get_secret(account_name, key):
    return keyring.get_password(KEYRING_SERVICE, f"{account_name}:{key}")


def delete_secret(account_name, key):
    try:
        keyring.delete_password(KEYRING_SERVICE, f"{account_name}:{key}")
    except PasswordDeleteError:
        pass


# ============================================================
# ACCOUNT MANAGEMENT
# ============================================================

def add_login(db, current_account=None):
    action_screen("ADD LOGIN", current_account)

    name = input("Account name / alias: ").strip()
    if not name:
        print("\n[x] Invalid account name.")
        pause()
        return None

    if name in db["accounts"]:
        print("\n[x] Account already exists.")
        pause()
        return None

    print("\nPaste the Steam credentials.")
    print("They will not be shown while typing.\n")

    steam_login_secure = getpass.getpass("steamLoginSecure: ").strip()
    session_id = getpass.getpass("sessionid: ").strip()
    api_key = getpass.getpass("Steam Web API Key: ").strip()

    if not steam_login_secure or not session_id or not api_key:
        print("\n[x] Missing credentials.")
        pause()
        return None

    save_secret(name, "steamLoginSecure", steam_login_secure)
    save_secret(name, "sessionid", session_id)
    save_secret(name, "api_key", api_key)

    db["accounts"][name] = {
        "tracked_sent": []
    }
    save_db(db)

    print(f"\n[+] Account '{name}' saved.")
    pause()
    return name


def select_account(db, current_account=None):
    accounts = list(db["accounts"].keys())

    action_screen("LOGIN ACCOUNT", current_account)

    if not accounts:
        print("[x] No accounts saved.")
        pause()
        return None

    for i, name in enumerate(accounts, 1):
        print(f"{i} - {name}")
    print("0 - Cancel")

    try:
        option = int(input("\n> ").strip())
        if option == 0:
            return None
        return accounts[option - 1]
    except (ValueError, IndexError):
        print("\n[x] Invalid option.")
        pause()
        return None


def delete_login(db, current_account=None):
    account_name = select_account(db, current_account)
    if not account_name:
        return False, None

    action_screen("DELETE LOGIN", current_account)
    confirm = input(f"Delete '{account_name}'? (y/n): ").strip().lower()
    if confirm != "y":
        return False, account_name

    for key in ("steamLoginSecure", "sessionid", "api_key"):
        delete_secret(account_name, key)

    db["accounts"].pop(account_name, None)
    save_db(db)

    print("\n[+] Account deleted.")
    pause()
    return True, account_name


# ============================================================
# STEAM SESSION
# ============================================================

def create_session(account_name):
    login_secure = get_secret(account_name, "steamLoginSecure")
    session_id = get_secret(account_name, "sessionid")
    api_key = get_secret(account_name, "api_key")

    if not login_secure or not session_id or not api_key:
        return None, None, "Missing saved credentials."

    session = requests.Session()
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept-Language": "en-US,en;q=0.9",
    })
    session.cookies.set("steamLoginSecure", login_secure, domain="steamcommunity.com")
    session.cookies.set("sessionid", session_id, domain="steamcommunity.com")

    return session, api_key, None


def validate_login(session):
    try:
        r = session.get(
            "https://steamcommunity.com/my/friends/pending?l=english",
            timeout=20,
            allow_redirects=True,
        )
    except requests.RequestException as e:
        return False, f"Connection error: {e}"

    final_url = r.url.lower()
    html_lower = r.text.lower()

    if "login" in final_url or "steamcommunity.com/login" in html_lower:
        return False, "steamLoginSecure/sessionid is invalid or expired."

    if r.status_code != 200:
        return False, f"Steam returned HTTP {r.status_code}."

    return True, None


# ============================================================
# URL HELPERS
# ============================================================

def normalize_group_url(group_url):
    group_url = group_url.strip().rstrip("/")

    # User may paste /members; strip it because XML endpoint is attached to group root.
    if group_url.endswith("/members"):
        group_url = group_url[:-8].rstrip("/")

    return group_url


def profile_slug_from_url(url):
    try:
        parsed = urlparse(url)
        parts = [p for p in parsed.path.split("/") if p]
        if len(parts) >= 2 and parts[0] in {"id", "profiles"}:
            return parts[0], parts[1]
    except Exception:
        pass
    return None, None


# ============================================================
# STEAM WEB API
# ============================================================

def vanity_to_steamid64(vanity, api_key):
    url = "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/"
    try:
        r = requests.get(
            url,
            params={"key": api_key, "vanityurl": vanity},
            headers={"User-Agent": USER_AGENT},
            timeout=20,
        )
        r.raise_for_status()
        data = r.json().get("response", {})
        if data.get("success") == 1:
            return data.get("steamid")
    except (requests.RequestException, ValueError):
        pass
    return None


def get_player_summaries(steam_ids, api_key):
    result = {}
    url = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"

    for start in range(0, len(steam_ids), 100):
        batch = steam_ids[start:start + 100]
        try:
            r = requests.get(
                url,
                params={"key": api_key, "steamids": ",".join(batch)},
                headers={"User-Agent": USER_AGENT},
                timeout=20,
            )
            r.raise_for_status()
            players = r.json().get("response", {}).get("players", [])
            for player in players:
                sid = str(player.get("steamid", ""))
                result[sid] = {
                    "name": player.get("personaname") or sid,
                    "profileurl": player.get("profileurl") or f"https://steamcommunity.com/profiles/{sid}",
                }
        except (requests.RequestException, ValueError):
            continue

    return result


# ============================================================
# GROUP MEMBERS - HTML FIRST, XML FALLBACK
# ============================================================

STEAMID64_BASE = 76561197960265728


def accountid_to_steamid64(account_id):
    try:
        account_id = int(account_id)
        if account_id < 0:
            return None
        return str(STEAMID64_BASE + account_id)
    except (TypeError, ValueError):
        return None


def _steamid_from_profile_href(href, api_key, vanity_cache):
    if not href:
        return None

    href = href.split("?", 1)[0].rstrip("/")
    kind, slug = profile_slug_from_url(href)

    if kind == "profiles" and slug and re.fullmatch(r"\d{17}", slug):
        return slug

    if kind == "id" and slug:
        if slug not in vanity_cache:
            vanity_cache[slug] = vanity_to_steamid64(slug, api_key)
        return vanity_cache[slug]

    return None


def _extract_member_ids_from_html(html, api_key, limit):
    soup = BeautifulSoup(html, "html.parser")
    found = []
    seen = set()
    vanity_cache = {}

    def add_sid(sid):
        if sid and re.fullmatch(r"\d{17}", str(sid)) and sid not in seen:
            seen.add(sid)
            found.append(str(sid))
            return True
        return False

    # Steam has historically wrapped each group member in a member_block.
    # We do NOT depend on the old linkFriend class, which is what broke the
    # previous scraper.
    blocks = soup.select(".member_block")

    # Try a couple of broader containers if Valve changes the wrapper name.
    if not blocks:
        blocks = soup.select("[class*='member_block'], [class*='memberRow'], [class*='member_row']")

    for block in blocks:
        # data-miniprofile is a Steam account ID (32-bit), not SteamID64.
        mini = block.find(attrs={"data-miniprofile": True})
        if mini:
            sid = accountid_to_steamid64(mini.get("data-miniprofile"))
            if add_sid(sid) and len(found) >= limit:
                return found

        # Fallback to the profile URL in the member row.
        for a in block.find_all("a", href=True):
            href = a.get("href", "")
            if "/id/" not in href and "/profiles/" not in href:
                continue
            sid = _steamid_from_profile_href(href, api_key, vanity_cache)
            if add_sid(sid):
                break

        if len(found) >= limit:
            return found

    # Last-resort fallback: use profile links from the public members page.
    # The page is fetched without login cookies, which avoids accidentally
    # including the logged-in account link from Steam's top navigation.
    if not found:
        for tag in soup.find_all(attrs={"data-miniprofile": True}):
            sid = accountid_to_steamid64(tag.get("data-miniprofile"))
            if add_sid(sid) and len(found) >= limit:
                return found

        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            if "steamcommunity.com/id/" not in href and "steamcommunity.com/profiles/" not in href:
                continue
            sid = _steamid_from_profile_href(href, api_key, vanity_cache)
            if add_sid(sid) and len(found) >= limit:
                return found

    return found


def get_group_members_html(group_url, max_users, api_key):
    group_url = normalize_group_url(group_url)
    members = []
    seen = set()
    page = 1

    # Intentionally do not reuse the authenticated Steam session here.
    # Group member pages are public, and this keeps account/profile links from
    # the logged-in header out of the generic HTML fallback.
    public_session = requests.Session()
    public_session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })

    while len(members) < max_users:
        url = f"{group_url}/members"

        try:
            r = public_session.get(
                url,
                params={"p": page, "l": "english"},
                timeout=25,
                allow_redirects=True,
            )
        except requests.RequestException as e:
            return members, f"Could not load group members page: {e}"

        if r.status_code == 429:
            retry_after = r.headers.get("Retry-After")
            extra = f" Retry-After: {retry_after}s." if retry_after else ""
            return members, (
                "Steam rate-limited the group members page (HTTP 429)."
                + extra
                + " Avoid repeated retries and try again later."
            )

        if r.status_code != 200:
            return members, f"Group members page returned HTTP {r.status_code}."

        page_ids = _extract_member_ids_from_html(
            r.text,
            api_key,
            max_users - len(members),
        )

        new_count = 0
        for sid in page_ids:
            if sid not in seen:
                seen.add(sid)
                members.append(sid)
                new_count += 1
                if len(members) >= max_users:
                    break

        if len(members) >= max_users:
            break

        if new_count == 0:
            break

        page += 1
        time.sleep(0.8)

    return members[:max_users], None


def get_group_members_xml(group_url, max_users=50):
    """Secondary fallback. Steam may rate-limit this endpoint aggressively."""
    group_url = normalize_group_url(group_url)
    members = []
    seen = set()
    page = 1

    while len(members) < max_users:
        xml_url = f"{group_url}/memberslistxml/"

        try:
            r = requests.get(
                xml_url,
                params={"xml": 1, "p": page},
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept": "application/xml,text/xml;q=0.9,*/*;q=0.8",
                },
                timeout=25,
            )
        except requests.RequestException as e:
            return members, f"Could not load group XML: {e}"

        if r.status_code == 429:
            return members, "Group XML endpoint returned HTTP 429 (rate limited)."

        if r.status_code != 200:
            return members, f"Group XML endpoint returned HTTP {r.status_code}."

        text = r.text.lstrip()
        if not text.startswith("<"):
            return members, "Steam did not return XML."

        try:
            root = ET.fromstring(r.text)
        except ET.ParseError:
            return members, "Steam returned invalid XML."

        page_ids = []
        for node in root.iter("steamID64"):
            sid = (node.text or "").strip()
            if re.fullmatch(r"\d{17}", sid):
                page_ids.append(sid)

        new_count = 0
        for sid in page_ids:
            if sid not in seen:
                seen.add(sid)
                members.append(sid)
                new_count += 1
                if len(members) >= max_users:
                    break

        if len(members) >= max_users or not page_ids or new_count == 0:
            break

        page += 1
        time.sleep(1.0)

    return members[:max_users], None


def get_group_members(group_url, max_users, api_key):
    # HTML is the primary path now because the XML endpoint commonly returns
    # 429 even when the normal public members page is accessible.
    members, html_error = get_group_members_html(group_url, max_users, api_key)
    if members:
        return members, None

    # If HTML itself was rate limited, do not hammer Steam with another request
    # family immediately.
    if html_error and "429" in html_error:
        return [], html_error

    xml_members, xml_error = get_group_members_xml(group_url, max_users)
    if xml_members:
        return xml_members, None

    errors = [e for e in (html_error, xml_error) if e]
    return [], " | ".join(errors) if errors else "Could not find group members."


# ============================================================
# FRIEND REQUESTS
# ============================================================

def parse_steam_response(response):
    try:
        data = response.json()
    except ValueError:
        data = None

    if not response.ok:
        return False, f"HTTP {response.status_code}"

    if isinstance(data, dict):
        success = data.get("success")
        if success in (True, 1, "1"):
            return True, data.get("message") or "OK"
        if success in (False, 0, "0"):
            return False, data.get("message") or str(data)

        # Some internal Steam endpoints return a JSON object without a success key.
        if data.get("steamid") or data.get("result") in (1, "1", True):
            return True, "OK"

    # Internal endpoint can return an empty/HTML 200 response.
    if response.status_code == 200 and not response.text.strip():
        return True, "OK"

    return response.status_code == 200, (response.text.strip()[:180] or "HTTP 200")


def add_friend(session, account_name, db, steam_id64, profile_url=None):
    profile_url = profile_url or f"https://steamcommunity.com/profiles/{steam_id64}"

    if not AUTO_MODE:
        confirm = input(f"Add {profile_url}? (y/n/q): ").strip().lower()
        if confirm == "q":
            return "quit"
        if confirm != "y":
            return False

    session_id = get_secret(account_name, "sessionid")
    url = "https://steamcommunity.com/actions/AddFriendAjax"

    try:
        r = session.post(
            url,
            data={"sessionID": session_id, "steamid": steam_id64},
            headers={"Referer": profile_url},
            timeout=20,
        )
    except requests.RequestException as e:
        print(f"    [x] Request error: {e}")
        return False

    ok, message = parse_steam_response(r)

    if ok:
        tracked = db["accounts"][account_name].setdefault("tracked_sent", [])
        if steam_id64 not in tracked:
            tracked.append(steam_id64)
            save_db(db)
        print(f"    [+] Friend request sent ({steam_id64})")
        return True

    print(f"    [x] Steam rejected request: {message}")
    return False


def cancel_friend_request(session, account_name, steam_id64):
    session_id = get_secret(account_name, "sessionid")
    profile_url = f"https://steamcommunity.com/profiles/{steam_id64}"
    url = "https://steamcommunity.com/actions/RemoveFriendAjax"

    try:
        r = session.post(
            url,
            data={"sessionID": session_id, "steamid": steam_id64},
            headers={"Referer": "https://steamcommunity.com/my/friends/pending"},
            timeout=20,
        )
    except requests.RequestException as e:
        return False, str(e)

    ok, message = parse_steam_response(r)
    return ok, message


# ============================================================
# REAL PENDING INVITES FROM STEAM PAGE
# ============================================================

def _extract_target_from_block(block, api_key):
    raw = str(block)

    # Best case: action HTML/JS includes SteamID64 directly.
    steam_ids = re.findall(r"(?<!\d)(7656119\d{10})(?!\d)", raw)
    if steam_ids:
        steam_id = steam_ids[-1]
    else:
        steam_id = None

    name = None
    profile_url = None

    for a in block.find_all("a", href=True):
        href = a.get("href", "")
        if "steamcommunity.com/id/" in href or "steamcommunity.com/profiles/" in href:
            profile_url = href.split("?")[0].rstrip("/")
            text = a.get_text(" ", strip=True)
            if text:
                name = text

            kind, slug = profile_slug_from_url(profile_url)
            if kind == "profiles" and slug and re.fullmatch(r"\d{17}", slug):
                steam_id = steam_id or slug
            elif kind == "id" and slug and not steam_id:
                steam_id = vanity_to_steamid64(slug, api_key)
            break

    if steam_id and not profile_url:
        profile_url = f"https://steamcommunity.com/profiles/{steam_id}"

    return steam_id, name or steam_id, profile_url


def get_real_sent_pending(session, api_key):
    url = "https://steamcommunity.com/my/friends/pending?l=english"

    try:
        r = session.get(url, timeout=25, allow_redirects=True)
    except requests.RequestException as e:
        return [], f"Could not load pending page: {e}"

    if "login" in r.url.lower():
        return [], "Steam cookies expired; pending page redirected to login."

    if r.status_code != 200:
        return [], f"Pending page returned HTTP {r.status_code}."

    soup = BeautifulSoup(r.text, "html.parser")
    results = {}

    # Steam's friends page has historically used search_results containers.
    containers = soup.select('[id*="search_results"]')
    candidate_blocks = []

    for container in containers:
        children = [child for child in container.find_all(recursive=False) if getattr(child, "name", None)]
        candidate_blocks.extend(children)

    # Fallback: common friend/pending row classes.
    if not candidate_blocks:
        candidate_blocks = soup.select(
            ".friend_block_v2, .friend_block, .search_result_row, .invite_row, [data-steamid]"
        )

    for block in candidate_blocks:
        raw = str(block)
        text = block.get_text(" ", strip=True)
        blob = (raw + " " + text).lower()

        # Outgoing invites normally have a cancel/remove action. Incoming rows
        # normally expose accept/ignore instead, so do not treat those as sent.
        looks_sent = any(marker in blob for marker in (
            "cancel invite",
            "cancel friend",
            "cancelrequest",
            "cancel_request",
            "removefriend",
            "remove friend",
            "cancel",
        ))
        looks_received = any(marker in blob for marker in (
            "accept invite",
            "accept friend",
            "ignore invite",
            "ignore friend",
        ))

        if not looks_sent or looks_received:
            continue

        sid, name, profile_url = _extract_target_from_block(block, api_key)
        if sid:
            results[sid] = {
                "steamid": sid,
                "name": name or sid,
                "profileurl": profile_url or f"https://steamcommunity.com/profiles/{sid}",
            }

    # Second fallback: inspect action elements directly and climb to their row.
    if not results:
        for tag in soup.find_all(["a", "button"]):
            raw = str(tag).lower()
            text = tag.get_text(" ", strip=True).lower()
            if not any(marker in (raw + " " + text) for marker in (
                "cancel", "removefriend", "remove friend"
            )):
                continue

            block = tag
            for _ in range(5):
                if getattr(block, "parent", None) is None:
                    break
                block = block.parent
                sid, name, profile_url = _extract_target_from_block(block, api_key)
                if sid:
                    results[sid] = {
                        "steamid": sid,
                        "name": name or sid,
                        "profileurl": profile_url or f"https://steamcommunity.com/profiles/{sid}",
                    }
                    break

    if results:
        return list(results.values()), None

    # Distinguish "zero pending" from "parser did not recognize page" as best we can.
    page_text = soup.get_text(" ", strip=True).lower()
    zero_markers = (
        "no pending invites",
        "no pending friend invites",
        "you have no pending",
        "no invites",
    )
    if any(marker in page_text for marker in zero_markers):
        return [], None

    return [], (
        "Steam page loaded, but no outgoing invite rows were recognized. "
        "This can mean there are no sent invites, or Valve changed the page markup."
    )


# ============================================================
# AUTO ADD
# ============================================================

def run_auto_add(session, account_name, api_key, db):
    action_screen("AUTO ADD FRIENDS", account_name)

    if DEFAULT_GROUP_URL:
        group = input(f"Group URL [{DEFAULT_GROUP_URL}]: ").strip() or DEFAULT_GROUP_URL
    else:
        group = input("Group URL: ").strip()

    if not group:
        print("\n[x] A Steam group URL is required.")
        pause()
        return

    try:
        value = input(f"Max users [{MAX_USERS}]: ").strip()
        max_users = int(value) if value else MAX_USERS
        if max_users <= 0:
            raise ValueError
    except ValueError:
        print("\n[x] Invalid amount.")
        pause()
        return

    print(f"\n[+] Loading first {max_users} members...")
    steam_ids, error = get_group_members(group, max_users, api_key)

    if error and not steam_ids:
        print(f"[x] {error}")
        pause()
        return

    if not steam_ids:
        print("[x] Found 0 members.")
        pause()
        return

    summaries = get_player_summaries(steam_ids, api_key)

    print(f"[+] Found {len(steam_ids)} members:\n")
    for i, sid in enumerate(steam_ids, 1):
        player = summaries.get(sid, {})
        name = player.get("name", sid)
        profile = player.get("profileurl", f"https://steamcommunity.com/profiles/{sid}")
        print(f"{i:>3}. {name}")
        print(f"     {profile}")

    print()
    start = input("Start sending requests? (y/n): ").strip().lower()
    if start != "y":
        pause()
        return

    sent = 0
    failed = 0

    for i, sid in enumerate(steam_ids, 1):
        player = summaries.get(sid, {})
        name = player.get("name", sid)
        profile = player.get("profileurl", f"https://steamcommunity.com/profiles/{sid}")

        print(f"\n[{i}/{len(steam_ids)}] {name}")
        result = add_friend(session, account_name, db, sid, profile)

        if result == "quit":
            break
        if result is True:
            sent += 1
        elif result is False:
            failed += 1

        time.sleep(REQUEST_DELAY)

    print("\n--- RESULT ---")
    print(f"Sent:   {sent}")
    print(f"Failed/skipped: {failed}")
    pause()


# ============================================================
# PENDING MENU
# ============================================================

def load_pending_for_display(session, account_name, api_key, db):
    real, warning = get_real_sent_pending(session, api_key)

    # If the Steam page was parsed successfully, trust Steam instead of the
    # local history. A locally tracked request may already have been accepted
    # or cancelled outside this script.
    if not warning:
        return real, None

    # Only use local history when Valve's pending-page markup could not be
    # recognized, so there is still a useful fallback.
    by_id = {item["steamid"]: item for item in real}
    tracked = db["accounts"][account_name].get("tracked_sent", [])

    missing = [sid for sid in tracked if sid not in by_id]
    if missing:
        summaries = get_player_summaries(missing, api_key)
        for sid in missing:
            player = summaries.get(sid, {})
            by_id[sid] = {
                "steamid": sid,
                "name": player.get("name", sid),
                "profileurl": player.get("profileurl", f"https://steamcommunity.com/profiles/{sid}"),
                "local_only": True,
            }

    return list(by_id.values()), warning


def view_pending(session, account_name, api_key, db):
    action_screen("SENT PENDING INVITES", account_name)

    pending, warning = load_pending_for_display(session, account_name, api_key, db)

    if warning:
        print(f"[!] {warning}\n")

    if not pending:
        print("No sent pending invites found.")
        pause()
        return

    for i, item in enumerate(pending, 1):
        suffix = " [local fallback]" if item.get("local_only") else ""
        print(f"{i:>3}. {item['name']}{suffix}")
        print(f"     {item['profileurl']}")
        print(f"     SteamID64: {item['steamid']}")

    print(f"\nTotal: {len(pending)}")
    pause()


def remove_pending(session, account_name, api_key, db):
    action_screen("REMOVE SENT PENDING INVITES", account_name)

    pending, warning = load_pending_for_display(session, account_name, api_key, db)

    if warning:
        print(f"[!] {warning}\n")

    if not pending:
        print("No sent pending invites found.")
        pause()
        return

    for i, item in enumerate(pending, 1):
        suffix = " [local fallback]" if item.get("local_only") else ""
        print(f"{i:>3}. {item['name']}{suffix}")
        print(f"     {item['profileurl']}")

    print("\nA - Remove ALL")
    print("0 - Cancel")
    choice = input("\nSelect number or A: ").strip().lower()

    if choice == "0":
        return

    if choice == "a":
        targets = pending
        confirm = input(f"Remove all {len(targets)} pending invites? (y/n): ").strip().lower()
        if confirm != "y":
            return
    else:
        try:
            index = int(choice) - 1
            targets = [pending[index]]
        except (ValueError, IndexError):
            print("\n[x] Invalid option.")
            pause()
            return

    tracked = db["accounts"][account_name].setdefault("tracked_sent", [])
    removed = 0

    for item in targets:
        sid = item["steamid"]
        print(f"\n[-] Removing {item['name']} ({sid})...")
        ok, message = cancel_friend_request(session, account_name, sid)
        if ok:
            print("    [+] Removed/cancelled.")
            removed += 1
            if sid in tracked:
                tracked.remove(sid)
                save_db(db)
        else:
            print(f"    [x] Failed: {message}")
        time.sleep(REQUEST_DELAY)

    print(f"\nRemoved: {removed}/{len(targets)}")
    pause()


# ============================================================
# MAIN
# ============================================================

def main():
    db = load_db()
    current_account = None
    session = None
    api_key = None

    while True:
        clear_screen()
        header(current_account)

        print("1 - Login Account")
        print("2 - Add Login")
        print("3 - Auto Add Friends")
        print("4 - Remove Pending Invites")
        print("5 - View Pending Invites")
        print("6 - Delete Login")
        print("0 - Exit")

        option = input("\n> ").strip()

        if option == "1":
            selected = select_account(db, current_account)
            if selected:
                new_session, new_api_key, error = create_session(selected)
                if error:
                    action_screen("LOGIN ERROR", current_account)
                    print(f"[x] {error}")
                    pause()
                    continue

                action_screen("CHECKING LOGIN", selected)
                ok, login_error = validate_login(new_session)
                if not ok:
                    print(f"[x] {login_error}")
                    print("\nUpdate the saved login if the Steam cookies expired.")
                    pause()
                    continue

                current_account = selected
                session = new_session
                api_key = new_api_key
                print(f"[+] Logged into saved profile: {selected}")
                pause()

        elif option == "2":
            account = add_login(db, current_account)
            if account:
                new_session, new_api_key, error = create_session(account)
                if not error:
                    ok, _ = validate_login(new_session)
                    if ok:
                        current_account = account
                        session = new_session
                        api_key = new_api_key

        elif option == "3":
            if not current_account:
                action_screen("AUTO ADD FRIENDS")
                print("[x] Login first.")
                pause()
                continue
            run_auto_add(session, current_account, api_key, db)

        elif option == "4":
            if not current_account:
                action_screen("REMOVE PENDING INVITES")
                print("[x] Login first.")
                pause()
                continue
            remove_pending(session, current_account, api_key, db)

        elif option == "5":
            if not current_account:
                action_screen("VIEW PENDING INVITES")
                print("[x] Login first.")
                pause()
                continue
            view_pending(session, current_account, api_key, db)

        elif option == "6":
            deleted, deleted_name = delete_login(db, current_account)
            if deleted and deleted_name == current_account:
                current_account = None
                session = None
                api_key = None

        elif option == "0":
            clear_screen()
            break

        else:
            action_screen("ERROR", current_account)
            print("[x] Invalid option.")
            pause()


if __name__ == "__main__":
    main()
