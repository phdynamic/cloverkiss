#!/usr/bin/env python3
"""Append new Bluesky posts from @cloverkisscinema.club to posts.json.

posts.json is a list of [rkey, "YYYY-MM-DD", text, is_reply]. Entries are only
ever appended, so the data-src indices in index.html keep pointing at the same
posts. Standard library only; the public API needs no login.
"""
import json
import sys
import urllib.parse
import urllib.request

HANDLE = "cloverkisscinema.club"
API = "https://public.api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed"
PATH = sys.argv[1] if len(sys.argv) > 1 else "posts.json"


def fetch_page(cursor):
    q = {"actor": HANDLE, "limit": "100", "filter": "posts_with_replies"}
    if cursor:
        q["cursor"] = cursor
    with urllib.request.urlopen(API + "?" + urllib.parse.urlencode(q), timeout=30) as r:
        return json.load(r)


def to_entry(item):
    if item.get("reason"):  # repost or pin, not an original post
        return None
    post = item["post"]
    if post["author"]["handle"] != HANDLE:
        return None
    rec = post["record"]
    text = rec.get("text", "")
    if not text:
        return None
    return [post["uri"].rsplit("/", 1)[-1], rec["createdAt"][:10], text, 1 if "reply" in rec else 0]


def main():
    with open(PATH, encoding="utf-8") as f:
        posts = json.load(f)
    known = {p[0] for p in posts}
    newest = max(known)  # rkeys are time-ordered, so they sort chronologically
    found, cursor = {}, None
    for _ in range(50):
        data = fetch_page(cursor)
        feed = data.get("feed", [])
        for item in feed:
            e = to_entry(item)
            if e and e[0] not in known:
                found[e[0]] = e
        cursor = data.get("cursor")
        oldest = [e for e in map(to_entry, feed) if e]
        if not cursor or not feed or (oldest and min(e[0] for e in oldest) <= newest):
            break
    new = [found[k] for k in sorted(found) if k > newest]
    if not new:
        print("No new posts.")
        return
    posts.extend(new)
    with open(PATH, "w", encoding="utf-8") as f:
        f.write(json.dumps(posts, ensure_ascii=False, separators=(",", ":")) + "\n")
    print("Added %d new post(s)." % len(new))


if __name__ == "__main__":
    main()
