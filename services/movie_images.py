import json
import re
from datetime import datetime, timedelta
from urllib.parse import quote
from urllib.request import Request, urlopen

from flask import current_app

from db.mongo import get_collection


TMDB_SEARCH_URL = (
    "https://api.themoviedb.org/3/search/movie"
    "?api_key={api_key}&language=ko-KR&region=KR&include_adult=false&query={query}"
)
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"


def _slugify(value):
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower())
    return slug.strip("-")


def get_tmdb_movie_poster(title, force_refresh=False):
    collection = get_collection("external_media_cache")
    cache_key = f"tmdb:movie:{_slugify(title)}"
    cached = collection.find_one({"cache_key": cache_key})
    now = datetime.utcnow()

    if cached and cached.get("generated_at") and cached["generated_at"] > now - timedelta(days=14) and not force_refresh:
        return cached.get("poster_url")

    api_key = current_app.config["TMDB_API_KEY"]
    request = Request(
        TMDB_SEARCH_URL.format(api_key=api_key, query=quote(title)),
        headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
    )

    poster_url = None
    try:
        with urlopen(request, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        for result in payload.get("results", []):
            poster_path = result.get("poster_path")
            if poster_path:
                poster_url = f"{TMDB_IMAGE_BASE_URL}{poster_path}"
                break
    except Exception:
        poster_url = cached.get("poster_url") if cached else None

    collection.update_one(
        {"cache_key": cache_key},
        {
            "$set": {
                "cache_key": cache_key,
                "source": "tmdb_search_movie",
                "title": title,
                "poster_url": poster_url,
                "generated_at": now,
            }
        },
        upsert=True,
    )
    return poster_url
