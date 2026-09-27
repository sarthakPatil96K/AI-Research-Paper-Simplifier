import json
import os
import re

META_DIR = "vector_db/metadata"
SUMM_DIR = "storage/summaries"

JUNK_AUTHORS = {"", "unknown", "untitled", "microsoft word", "admin"}

updated = 0
for fname in os.listdir(META_DIR):
    if not fname.endswith(".json"):
        continue
    paper_id = fname[:-5]
    path = os.path.join(META_DIR, fname)

    with open(path) as f:
        data = json.load(f)

    meta = data.setdefault("metadata", {})
    changed = False

    # --- Title cleanup ---
    title = (meta.get("title") or "").strip()
    if title.lower().startswith("title:"):
        title = title[6:].strip()
        changed = True

    if not title or title.lower() == "untitled":
        spath = os.path.join(SUMM_DIR, f"{paper_id}.json")
        if os.path.exists(spath):
            with open(spath) as f:
                sdata = json.load(f)
            stitle = (sdata.get("summary") or {}).get("title")
            if stitle:
                title = stitle.strip()
                changed = True

    if title and title != meta.get("title"):
        meta["title"] = title
        changed = True

    # --- Author cleanup ---
    author = (meta.get("author") or "").strip()
    if author.lower() in JUNK_AUTHORS:
        meta["author"] = "Unknown"
        changed = True

    if changed:
        with open(path, "w") as f:
            json.dump(data, f, indent=4)
        print(f"✓ {paper_id}  →  {meta.get('title')}  /  {meta.get('author')}")
        updated += 1

print(f"\nDone. {updated} papers updated.")