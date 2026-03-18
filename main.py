import os
import json
import requests
import time
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL")
ENV = os.getenv("ENV")

def load_state():
    try:
        with open("state.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

def save_state(state: dict):
    with open("state.json", "w") as f:
        json.dump(state, f, indent=2)

def fetch_repo_events_once():
    owner = os.getenv("REPO_OWNER")
    repo = os.getenv("REPO_NAME")

    print(f"START job=fetch_repo_events_once repo={owner}/{repo} env={ENV}")

    r = requests.get(
        f"{BASE_URL}/repos/{owner}/{repo}/events",
        headers={"Accept": "application/vnd.github+json"},
        timeout=5,
    )
    r.raise_for_status()

    events = r.json()
    print(f"OK status={r.status_code} events={len(events)}")

    with open("output.json", "w") as f:
        json.dump(events, f, indent=2)

    print("DONE file=output.json")

def github_get(path: str, params=None, retries: int = 1):
    url = f"{BASE_URL}{path}"
    headers = {"Accept": "application/vnd.github+json"}

    for attempt in range(retries + 1):
        r = requests.get(url, params=params, headers=headers, timeout=5)

        # Happy path
        if 200 <= r.status_code < 300:
            return r

        # Rate limit handling (common GitHub pattern: 403 with Remaining=0)
        remaining = r.headers.get("X-RateLimit-Remaining")
        reset = r.headers.get("X-RateLimit-Reset")
        retry_after = r.headers.get("Retry-After")

        is_rate_limited = (
            r.status_code in (403, 429)
            and (
                (remaining is not None and remaining == "0")
                or retry_after is not None
            )
        )

        if is_rate_limited and attempt < retries:
            # Prefer Retry-After if present
            if retry_after is not None:
                wait = int(retry_after)
            elif reset is not None:
                wait = max(0, int(reset) - int(time.time())) + 1
            else:
                wait = 5  # fallback

            print(f"RATE_LIMIT status={r.status_code} wait={wait}s attempt={attempt+1}/{retries}")
            time.sleep(wait)
            continue

        # Other errors: fail loud
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"HTTP_ERROR status={r.status_code} url={r.url} err={e}")
        return None

    return None

def detect_new_events(events, last_id):
    new_events = []
    last = int(last_id) if last_id is not None else None

    for e in events:
        eid = int(e["id"])

        if last is None or eid > last:
            new_events.append(e)

    return new_events

def fetch_new_events():
    owner = os.getenv("REPO_OWNER")
    repo = os.getenv("REPO_NAME")

    state = load_state()
    last_id = state.get("last_event_id")  # string or None

    print(f"START job=fetch_new_events repo={owner}/{repo} env={ENV} last_event_id={last_id}")

    r = requests.get(
        f"{BASE_URL}/repos/{owner}/{repo}/events",
        headers={"Accept": "application/vnd.github+json"},
        timeout=5,
    )
    r.raise_for_status()

    events = r.json()

    # GitHub returns newest first
    
    new_events = detect_new_events(events, last_id)

    # update checkpoint to newest seen (first item)

    with open("output.json", "w") as f:
        json.dump(new_events, f, indent=2)
    # update checkpoint AFTER successful output write
    if events:
        state["last_event_id"] = events[0]["id"]
        save_state(state)

    print(f"OK status={r.status_code} fetched={len(events)} new={len(new_events)} saved_last_event_id={state.get('last_event_id')}")
    print("DONE file=output.json state=state.json")

if __name__ == "__main__":
    fetch_new_events()