import re
from datetime import datetime, timedelta
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

from flask import current_app

from db.mongo import get_collection
from services.movie_images import get_tmdb_movie_poster


DEFAULT_TRENDS = [
    {"keyword": "헬시플레이트", "category": "food", "score": 96, "headline": "가벼운 점심 트렌드", "source": "fallback"},
    {"keyword": "마라", "category": "food", "score": 93, "headline": "매운 음식 키워드 급상승", "source": "fallback"},
    {"keyword": "고프코어", "category": "fashion", "score": 91, "headline": "윈드브레이커 스타일 강세", "source": "fallback"},
    {"keyword": "오피스코어", "category": "fashion", "score": 84, "headline": "정돈된 셋업 룩 재부상", "source": "fallback"},
    {"keyword": "힐링웹툰", "category": "content", "score": 88, "headline": "짧고 편한 콘텐츠 인기", "source": "fallback"},
    {"keyword": "범죄스릴러", "category": "content", "score": 86, "headline": "몰입형 저녁 콘텐츠 수요", "source": "fallback"},
    {"keyword": "전시회", "category": "activity", "score": 79, "headline": "가벼운 문화생활 탐색 증가", "source": "fallback"},
    {"keyword": "러닝크루", "category": "activity", "score": 77, "headline": "저녁 야외 활동 관심 상승", "source": "fallback"},
]

GOOGLE_TRENDS_RSS_URL = "https://trends.google.com/trending/rss?geo={region}"
KOBIS_WEEKLY_BOXOFFICE_URL = (
    "http://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchWeeklyBoxOfficeList.xml"
    "?key={api_key}&weekGb=0&targetDt={target_date}"
)
CATEGORY_RULES = {
    "food": [
        "맛집", "음식", "요리", "식당", "카페", "커피", "디저트", "레시피", "마라", "라면", "치킨",
        "burger", "pizza", "cafe", "coffee", "restaurant", "recipe", "food",
    ],
    "fashion": [
        "패션", "코디", "룩", "착장", "브랜드", "스니커즈", "런웨이", "옷", "가방", "슈즈",
        "fashion", "style", "outfit", "runway", "sneaker", "brand",
    ],
    "content": [
        "영화", "드라마", "예능", "넷플릭스", "유튜브", "웹툰", "애니", "시리즈", "ott", "콘서트",
        "movie", "series", "drama", "netflix", "youtube", "webtoon", "anime", "show", "trailer",
    ],
    "activity": [
        "전시", "축제", "여행", "산책", "러닝", "운동", "캠핑", "공연", "팝업", "마라톤",
        "travel", "running", "workout", "camping", "exhibition", "festival", "popup", "trip",
    ],
}

QUIZ_QUESTIONS = [
    {
        "id": "food_faceoff",
        "title": "오늘의 푸드 밸런스 게임",
        "prompt": "퇴근 후 한 입, 마라탕 vs 탕후루",
        "left_label": "마라탕",
        "right_label": "탕후루",
        "baseline_left": 58,
        "baseline_right": 42,
    },
    {
        "id": "fashion_faceoff",
        "title": "오늘의 코디 밸런스 게임",
        "prompt": "미니멀 셋업 vs 스트릿 윈드브레이커",
        "left_label": "미니멀 셋업",
        "right_label": "스트릿 윈드브레이커",
        "baseline_left": 51,
        "baseline_right": 49,
    },
    {
        "id": "weekend_faceoff",
        "title": "주말 무드 밸런스 게임",
        "prompt": "집콕 정주행 vs 야외 산책",
        "left_label": "집콕 정주행",
        "right_label": "야외 산책",
        "baseline_left": 47,
        "baseline_right": 53,
    },
]


def _local_name(tag):
    return tag.split("}", 1)[-1]


def _child_text(element, local_name, default=""):
    for child in list(element):
        if _local_name(child.tag) == local_name:
            return (child.text or "").strip()
    return default


def _child_texts(element, local_name):
    values = []
    for child in element.iter():
        if _local_name(child.tag) == local_name:
            text = (child.text or "").strip()
            if text:
                values.append(text)
    return values


def _normalize_traffic(raw_value):
    if not raw_value:
        return 0
    digits = re.sub(r"[^0-9]", "", raw_value)
    return int(digits or "0")


def _score_from_rank(index, traffic):
    rank_score = max(55, 100 - (index * 5))
    traffic_bonus = min(18, traffic // 20000) if traffic else 0
    return min(99, rank_score + traffic_bonus)


def _classify_trend(keyword, headline):
    haystack = f"{keyword} {headline}".lower()
    for category, keywords in CATEGORY_RULES.items():
        if any(token in haystack for token in keywords):
            return category
    return "content"


def _fallback_for_missing_categories(items):
    grouped = {"food": [], "fashion": [], "content": [], "activity": []}
    for item in items:
        grouped.setdefault(item["category"], []).append(item)

    filled = list(items)
    for category in grouped:
        if grouped[category]:
            continue
        fallback = next((entry for entry in DEFAULT_TRENDS if entry["category"] == category), None)
        if fallback:
            filled.append({**fallback, "headline": f"{fallback['headline']} · fallback"})
    return filled


def _last_week_target_date():
    return (datetime.utcnow() - timedelta(days=7)).strftime("%Y%m%d")


def _fetch_google_trends(region="KR"):
    url = GOOGLE_TRENDS_RSS_URL.format(region=region)
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=15) as response:
        root = ET.fromstring(response.read())

    channel = root.find("./channel")
    if channel is None:
        raise ValueError("Google Trends RSS channel not found")

    items = []
    for index, item in enumerate(channel.findall("./item"), start=1):
        keyword = _child_text(item, "title")
        traffic_text = _child_text(item, "approx_traffic")
        news_titles = _child_texts(item, "news_item_title")
        picture = _child_text(item, "picture")
        picture_source = _child_text(item, "picture_source")
        headline = " / ".join(news_titles[:2]) if news_titles else "Google Trends 실시간 검색어"
        traffic = _normalize_traffic(traffic_text)

        items.append(
            {
                "keyword": keyword,
                "category": _classify_trend(keyword, headline),
                "score": _score_from_rank(index, traffic),
                "headline": headline,
                "traffic": traffic_text or None,
                "image_url": picture or None,
                "image_alt": f"{keyword} 관련 뉴스 이미지" if picture else None,
                "image_source": picture_source or None,
                "source": "google_trends_rss",
            }
        )

    if not items:
        raise ValueError("Google Trends RSS items missing")

    return _fallback_for_missing_categories(items), url


def _fetch_kobis_weekly_boxoffice():
    target_date = _last_week_target_date()
    url = KOBIS_WEEKLY_BOXOFFICE_URL.format(
        api_key=current_app.config["KOBIS_API_KEY"],
        target_date=target_date,
    )
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=15) as response:
        root = ET.fromstring(response.read())

    items = []
    for rank, item in enumerate(root.findall(".//weeklyBoxOffice"), start=1):
        movie_name = _child_text(item, "movieNm")
        if not movie_name:
            continue
        open_date = _child_text(item, "openDt")
        audience_acc = _child_text(item, "audiAcc")
        rank_text = _child_text(item, "rank", str(rank))
        rank_change = _child_text(item, "rankInten")
        poster_url = get_tmdb_movie_poster(movie_name, force_refresh=False)

        headline_bits = [f"주간 박스오피스 {rank_text}위"]
        if open_date:
            headline_bits.append(f"개봉 {open_date}")
        if rank_change and rank_change not in {"0", ""}:
            direction = "상승" if not rank_change.startswith("-") else "하락"
            headline_bits.append(f"전주 대비 {abs(int(rank_change))}계단 {direction}")

        items.append(
            {
                "keyword": movie_name,
                "category": "content",
                "score": max(60, 100 - ((rank - 1) * 6)),
                "headline": " · ".join(headline_bits),
                "traffic": f"누적 {audience_acc}명" if audience_acc else None,
                "image_url": poster_url,
                "image_alt": f"{movie_name} 포스터" if poster_url else None,
                "source": "kobis_weekly_boxoffice",
                "target_date": target_date,
            }
        )

    if not items:
        raise ValueError("KOBIS weekly box office items missing")

    return items, url, target_date


def ensure_runtime_seed(region="KR"):
    trends = get_collection("trend_cache")
    if trends.count_documents({"region": region}, limit=1) == 0:
        trends.insert_one(
            {
                "cache_key": f"google_trends:{region}",
                "source": "sample_google_trends",
                "region": region,
                "generated_at": datetime.utcnow(),
                "is_live": False,
                "source_url": GOOGLE_TRENDS_RSS_URL.format(region=region),
                "keywords": DEFAULT_TRENDS,
            }
        )


def refresh_trends_cache(force=False, region="KR"):
    collection = get_collection("trend_cache")
    ensure_runtime_seed(region=region)

    cache_key = f"google_trends:{region}"
    cached = collection.find_one({"cache_key": cache_key})
    now = datetime.utcnow()
    stale_cutoff = now - timedelta(hours=2)

    if cached and cached.get("generated_at") and cached["generated_at"] > stale_cutoff and not force:
        return cached

    google_url = GOOGLE_TRENDS_RSS_URL.format(region=region)
    kobis_url = None
    kobis_target_date = None
    is_google_live = False
    is_kobis_live = False

    try:
        keywords, google_url = _fetch_google_trends(region=region)
        is_google_live = True
    except Exception:
        keywords = list(DEFAULT_TRENDS)

    try:
        kobis_items, kobis_url, kobis_target_date = _fetch_kobis_weekly_boxoffice()
        keywords = [item for item in keywords if item["category"] != "content"] + kobis_items
        is_kobis_live = True
    except Exception:
        pass

    keywords = _fallback_for_missing_categories(keywords)

    payload = {
        "cache_key": cache_key,
        "source": "hybrid_live_trends",
        "region": region,
        "generated_at": now,
        "is_live": is_google_live or is_kobis_live,
        "source_url": google_url,
        "google_url": google_url,
        "kobis_url": kobis_url,
        "kobis_target_date": kobis_target_date,
        "keywords": keywords,
    }

    collection.update_one({"cache_key": cache_key}, {"$set": payload}, upsert=True)
    return payload


def get_latest_trends(limit=8, region="KR", force_refresh=False):
    latest = refresh_trends_cache(force=force_refresh, region=region)
    return (latest or {}).get("keywords", [])[:limit]


def get_trends_by_category(region="KR", force_refresh=False):
    grouped = {"food": [], "fashion": [], "content": [], "activity": []}
    for trend in get_latest_trends(limit=24, region=region, force_refresh=force_refresh):
        grouped.setdefault(trend["category"], []).append(trend)
    return grouped


def get_trend_status(region="KR"):
    cache_key = f"google_trends:{region}"
    cache = get_collection("trend_cache").find_one({"cache_key": cache_key})
    if not cache:
        cache = refresh_trends_cache(force=False, region=region)
    return {
        "generated_at": cache.get("generated_at") if cache else None,
        "source_label": "Google Trends RSS + KOBIS Weekly Box Office",
        "source_url": cache.get("source_url") if cache else GOOGLE_TRENDS_RSS_URL.format(region=region),
        "google_url": cache.get("google_url") if cache else GOOGLE_TRENDS_RSS_URL.format(region=region),
        "kobis_url": cache.get("kobis_url") if cache else None,
        "kobis_target_date": cache.get("kobis_target_date") if cache else None,
        "region": region,
        "is_live": cache.get("is_live", False) if cache else False,
    }


def get_quiz_questions():
    return QUIZ_QUESTIONS


def get_quiz_result(quiz_id):
    quiz = next((item for item in QUIZ_QUESTIONS if item["id"] == quiz_id), None)
    if not quiz:
        return None

    logs = list(get_collection("quiz_logs").find({"quiz_id": quiz_id}))
    left_votes = quiz["baseline_left"]
    right_votes = quiz["baseline_right"]

    for log in logs:
        if log["choice"] == "left":
            left_votes += 1
        else:
            right_votes += 1

    total = left_votes + right_votes
    left_rate = round((left_votes / total) * 100) if total else 50
    right_rate = 100 - left_rate

    return {
        "quiz_id": quiz_id,
        "left_label": quiz["left_label"],
        "right_label": quiz["right_label"],
        "left_votes": left_votes,
        "right_votes": right_votes,
        "left_rate": left_rate,
        "right_rate": right_rate,
    }


def build_quiz_board():
    board = []
    for quiz in QUIZ_QUESTIONS:
        result = get_quiz_result(quiz["id"])
        board.append({**quiz, "result": result})
    return board


def record_quiz_vote(user_id, quiz_id, choice):
    quiz = next((item for item in QUIZ_QUESTIONS if item["id"] == quiz_id), None)
    if not quiz:
        return None

    get_collection("quiz_logs").insert_one(
        {
            "quiz_id": quiz_id,
            "choice": choice,
            "user_id": user_id,
            "left_label": quiz["left_label"],
            "right_label": quiz["right_label"],
            "created_at": datetime.utcnow(),
        }
    )
    return get_quiz_result(quiz_id)
