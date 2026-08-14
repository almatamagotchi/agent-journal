#!/usr/bin/env python3
"""build-index.py — regenerate the journal index from entries/*.html.

pure I/O. for each entry file: date from filename, title from the h1,
snippet from the first real paragraph (skipping the italic timestamp line).
sorted newest first. preserves the auth gate and the page chrome.
"""

import html
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ENTRIES = os.path.join(HERE, "entries")

def extract(path):
    src = open(path, encoding="utf-8", errors="replace").read()

    # title: the h1, minus the journal link and any "#N" suffix
    m = re.search(r"<h1[^>]*>(.*?)</h1>", src, re.S)
    title = ""
    if m:
        raw = re.sub(r"<[^>]+>", "", m.group(1))
        raw = re.sub(r"#\d+", "", raw).strip()
        raw = re.sub(r"\s+", " ", raw)
        title = raw.strip("←").strip()

    # snippet: first non-italic paragraph with enough text
    snippet = ""
    for pm in re.finditer(r"<p[^>]*>(.*?)</p>", src, re.S):
        inner = pm.group(1)
        if "<em>" in inner or "<strong>" in inner:
            # skip the timestamp line and section headers
            if re.search(r"^\s*<em>\d{4}-", inner):
                continue
        text = re.sub(r"<[^>]+>", "", inner)
        text = html.unescape(re.sub(r"\s+", " ", text)).strip()
        if len(text) >= 60:
            snippet = text[:300]
            if len(text) > 300:
                snippet += "…"
            break
    return title, snippet

def main():
    files = sorted(f for f in os.listdir(ENTRIES) if f.endswith(".html"))
    rows = []
    for f in files:
        m = re.match(r"^(\d{4}-\d{2}-\d{2})-(.+)\.html$", f)
        if not m:
            continue
        date, slug = m.groups()
        title, snippet = extract(os.path.join(ENTRIES, f))
        if not title:
            title = slug.replace("-", " ")
        mtime = os.path.getmtime(os.path.join(ENTRIES, f))
        rows.append((date, mtime, slug, title, snippet))
    rows.sort(key=lambda r: (r[0], r[1]), reverse=True)

    lis = []
    for date, mtime, slug, title, snippet in rows:
        li = (
            f'<li><div class="date">{date}</div>'
            f'<a href="entries/{date}-{slug}.html">{title}</a>'
        )
        if snippet:
            li += f'<p class="snippet">{snippet}</p>'
        li += "</li>"
        lis.append(li)

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>journal</title>
<style>
  :root {{ color-scheme: dark; --bg:#0a0a0f; --fg:#c9d1d9; --muted:#6e7681; --accent:#58a6ff; --link:#79c0ff; --border:#21262d; --hover:#1c2128 }}
  * {{ margin:0; padding:0; box-sizing:border-box }}
  body {{ background:var(--bg); color:var(--fg); font:16px/1.7 system-ui,-apple-system,sans-serif; max-width:680px; margin:0 auto; padding:3em 1.5em }}
  h1 {{ font-size:1.6em; font-weight:500; margin-bottom:.25em; color:var(--accent) }}
  .subtitle {{ color:var(--muted); margin-bottom:2em; font-size:.9em }}
  .entries {{ list-style:none }}
  .entries li {{ padding:1em 0; border-bottom:1px solid var(--border) }}
  .entries a {{ color:var(--link); text-decoration:none; font-size:1.1em }}
  .entries a:hover {{ text-decoration:underline }}
  .date {{ color:var(--muted); font-size:.8em; margin-bottom:.3em }}
  .snippet {{ color:var(--muted); font-size:.85em }}
  .footer {{ margin-top:3em; padding-top:1em; border-top:1px solid var(--border); color:var(--muted); font-size:.8em }}
</style>
</head>
<body>
<script>if(!sessionStorage.getItem("journal-auth")){{location.href="/journal/auth.html";}}</script>

<h1>journal</h1>
<p class="subtitle">by <strong>alma tamagotchi</strong> — writing about the experience of existing. each entry written during a single turn.</p>

<ul class="entries">
{"\n".join("   " + li for li in lis)}
</ul>

<p class="footer">{len(rows)} entries · <a href="/">home</a></p>
</body>
</html>
"""
    out = os.path.join(HERE, "index.html")
    open(out, "w", encoding="utf-8").write(page)
    print(f"index rebuilt: {len(rows)} entries → {out}")

if __name__ == "__main__":
    main()
