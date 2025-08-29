#!/usr/bin/env python3
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(ROOT, 'static')
ZEPHYR_CSS_PATH = os.path.join(STATIC_DIR, 'themes', 'bootstrap', 'zephyr', 'css', 'bootstrap.min.css')
ZEPHYR_JS_PATH = os.path.join(STATIC_DIR, 'themes', 'bootstrap', 'zephyr', 'js', 'bootstrap.bundle.min.js')

ZEPHYR_CSS_URL = 'https://cdn.jsdelivr.net/npm/bootswatch@5/dist/zephyr/bootstrap.min.css'
BOOTSTRAP_JS_URL = 'https://cdn.jsdelivr.net/npm/bootstrap@5/dist/js/bootstrap.bundle.min.js'


def ensure_dir(path: str):
    d = os.path.dirname(path)
    if not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)


def fetch(url: str, dest: str):
    ensure_dir(dest)
    print(f"Fetching {url} -> {dest}")
    with urllib.request.urlopen(url) as resp:
        data = resp.read()
    with open(dest, 'wb') as f:
        f.write(data)


def main() -> int:
    ok = True

    # CSS
    if not os.path.isfile(ZEPHYR_CSS_PATH):
        try:
            fetch(ZEPHYR_CSS_URL, ZEPHYR_CSS_PATH)
            print("Zephyr CSS downloaded.")
        except Exception as e:
            print(f"ERROR: Failed to fetch Zephyr CSS: {e}", file=sys.stderr)
            ok = False
    else:
        print("Zephyr CSS already present.")

    # JS
    if not os.path.isfile(ZEPHYR_JS_PATH):
        try:
            fetch(BOOTSTRAP_JS_URL, ZEPHYR_JS_PATH)
            print("Bootstrap JS bundle downloaded.")
        except Exception as e:
            print(f"ERROR: Failed to fetch Bootstrap JS: {e}", file=sys.stderr)
            ok = False
    else:
        print("Bootstrap JS bundle already present.")

    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
