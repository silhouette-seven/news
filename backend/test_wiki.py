import requests
import json
url = "https://en.wikipedia.org/w/api.php"
params = {
    "action": "query",
    "format": "json",
    "prop": "pageimages",
    "piprop": "original|thumbnail",
    "pithumbsize": "600",
    "generator": "search",
    "gsrsearch": "Finance",
    "gsrlimit": "5"
}
headers = {'User-Agent': "AntigravityNewsBot/1.0"}
try:
    r = requests.get(url, params=params, headers=headers).json()
    urls = []
    for p in r.get('query', {}).get('pages', {}).values():
        img = p.get('thumbnail', {}).get('source') or p.get('original', {}).get('source')
        if img:
            urls.append((p.get('title'), img))
    print("URLS:", urls)
except Exception as e:
    print("Error:", e)
