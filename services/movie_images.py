import json
import re
import hashlib
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
WIKIPEDIA_SUMMARY_URL = (
    "https://ko.wikipedia.org/w/api.php"
    "?action=query&format=json&formatversion=2&prop=pageimages&piprop=thumbnail&pithumbsize=600&titles={title}"
)
WIKIPEDIA_SEARCH_URL = (
    "https://ko.wikipedia.org/w/api.php"
    "?action=query&format=json&formatversion=2&list=search&srlimit=1&srsearch={query}"
)
WIKIPEDIA_PAGE_BY_ID_URL = (
    "https://ko.wikipedia.org/w/api.php"
    "?action=query&format=json&formatversion=2&prop=pageimages&piprop=thumbnail&pithumbsize=600&pageids={page_id}"
)


def _slugify(value):
    normalized = (value or "").strip().lower()
    slug = re.sub(r"[^\w]+", "-", normalized, flags=re.UNICODE).strip("-_").replace("_", "-")
    if slug:
        return slug
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:12]


def _normalize_title(value):
    return re.sub(r"[^\w]+", "", (value or "").strip().lower(), flags=re.UNICODE)


def _select_best_tmdb_result(title, results):
    target = _normalize_title(title)
    best_result = None
    best_score = -1

    for result in results or []:
        poster_path = result.get("poster_path")
        candidates = [
            result.get("title"),
            result.get("original_title"),
            result.get("name"),
            result.get("original_name"),
        ]
        candidate_tokens = [_normalize_title(candidate) for candidate in candidates if candidate]
        score = 0

        if any(candidate == target for candidate in candidate_tokens):
            score += 100
        elif any(target and candidate and (target in candidate or candidate in target) for candidate in candidate_tokens):
            score += 60

        if poster_path:
            score += 20

        score += min(int(result.get("popularity", 0) or 0), 15)

        if score > best_score:
            best_score = score
            best_result = result

    return best_result


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
        best_result = _select_best_tmdb_result(title, payload.get("results", []))
        poster_path = (best_result or {}).get("poster_path")
        if poster_path:
            poster_url = f"{TMDB_IMAGE_BASE_URL}{poster_path}"
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


def _wikipedia_thumbnail_from_page_payload(payload):
    pages = payload.get("query", {}).get("pages", [])
    for page in pages:
        thumbnail = page.get("thumbnail", {})
        source = thumbnail.get("source")
        if source:
            return source
    return None


def get_wikipedia_webtoon_image(title, force_refresh=False):
    collection = get_collection("external_media_cache")
    cache_key = f"wikipedia:webtoon:{_slugify(title)}"
    cached = collection.find_one({"cache_key": cache_key})
    now = datetime.utcnow()

    if cached and cached.get("generated_at") and cached["generated_at"] > now - timedelta(days=14) and not force_refresh:
        return cached.get("image_url")

    image_url = None
    try:
        summary_request = Request(
            WIKIPEDIA_SUMMARY_URL.format(title=quote(title)),
            headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
        )
        with urlopen(summary_request, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        image_url = _wikipedia_thumbnail_from_page_payload(payload)

        if not image_url:
            search_request = Request(
                WIKIPEDIA_SEARCH_URL.format(query=quote(f"{title} 웹툰")),
                headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
            )
            with urlopen(search_request, timeout=5) as response:
                search_payload = json.loads(response.read().decode("utf-8"))

            search_results = search_payload.get("query", {}).get("search", [])
            if search_results:
                page_id = search_results[0].get("pageid")
                if page_id:
                    page_request = Request(
                        WIKIPEDIA_PAGE_BY_ID_URL.format(page_id=page_id),
                        headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
                    )
                    with urlopen(page_request, timeout=5) as response:
                        page_payload = json.loads(response.read().decode("utf-8"))
                    image_url = _wikipedia_thumbnail_from_page_payload(page_payload)
    except Exception:
        image_url = cached.get("image_url") if cached else None

    collection.update_one(
        {"cache_key": cache_key},
        {
            "$set": {
                "cache_key": cache_key,
                "source": "wikipedia_webtoon_image",
                "title": title,
                "image_url": image_url,
                "generated_at": now,
            }
        },
        upsert=True,
    )
    return image_url
