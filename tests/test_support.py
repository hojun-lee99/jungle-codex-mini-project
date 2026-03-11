from datetime import datetime
from uuid import uuid4

from config import Config


Config.MONGO_URI = "mongodb://127.0.0.1:1/"
Config.USE_MOCK_ON_FAILURE = True
Config.DEBUG = False

from app import create_app  # noqa: E402
from db.mongo import get_collection, get_db, mongo  # noqa: E402
from services.account import create_user  # noqa: E402
from services.profile_service import ensure_profile  # noqa: E402
from services.trends import ensure_runtime_seed  # noqa: E402


TEST_APP = create_app()
TEST_APP.config.update(TESTING=True)


def seed_content_source_cache():
    collection = get_collection("content_source_cache")
    now = datetime.utcnow()

    collection.update_one(
        {"cache_key": "netflix_top10_kr_movies"},
        {
            "$set": {
                "cache_key": "netflix_top10_kr_movies",
                "generated_at": now,
                "period_label": "South Korea | 03/01/26 - 03/07/26",
                "source_url": "https://example.com/netflix",
                "items": [
                    {
                        "id": "netflix:test:midnight-run",
                        "name": "미드나이트 런",
                        "description": "속도감 있게 보기 좋은 넷플릭스 인기 액션 영화입니다.",
                        "genres": ["액션", "범죄"],
                        "platforms": ["넷플릭스"],
                        "provider": "Netflix",
                        "content_type": "영화",
                        "moods": ["focus", "reward", "dark"],
                        "trend_keywords": ["넷플릭스영화", "액션영화"],
                        "duration_label": "한국 Top 10 영화",
                        "freshness_boost": 8,
                        "source": "netflix_tudum",
                        "image_url": "https://example.com/netflix-midnight-run.jpg",
                        "source_url": "https://example.com/netflix-midnight-run",
                        "external_url": "https://example.com/watch/midnight-run",
                        "stats": {"rank": 1, "weeks_in_top10": 2, "country": "South Korea"},
                    }
                ],
            }
        },
        upsert=True,
    )

    collection.update_one(
        {"cache_key": "kobis_weekly_boxoffice"},
        {
            "$set": {
                "cache_key": "kobis_weekly_boxoffice",
                "generated_at": now,
                "target_date": "20260307",
                "source_url": "https://example.com/kobis",
                "items": [
                    {
                        "id": "kobis:test:seoul-spring",
                        "name": "서울의 봄",
                        "description": "국내 박스오피스에서 반응이 좋은 한국 영화입니다.",
                        "genres": ["드라마", "스릴러"],
                        "platforms": ["영화"],
                        "provider": "KOBIS",
                        "content_type": "영화",
                        "moods": ["focus", "dark", "reward"],
                        "trend_keywords": ["박스오피스", "한국영화"],
                        "duration_label": "극장 화제작",
                        "freshness_boost": 7,
                        "source": "kobis_weekly",
                        "image_url": "https://example.com/kobis-seoul.jpg",
                        "source_url": "https://example.com/kobis-seoul",
                        "external_url": "https://example.com/watch/seoul",
                        "stats": {"rank": 2, "audience_acc": 1000000, "open_date": "2026-03-01"},
                    }
                ],
            }
        },
        upsert=True,
    )

    collection.update_one(
        {"cache_key": "tmdb_trending_movies"},
        {
            "$set": {
                "cache_key": "tmdb_trending_movies",
                "generated_at": now,
                "source_url": "https://example.com/tmdb-movies",
                "items": [
                    {
                        "id": "tmdb:movie:future-city",
                        "name": "퓨처 시티",
                        "description": "세계관과 비주얼이 강한 SF 영화입니다.",
                        "genres": ["SF", "모험"],
                        "platforms": ["영화"],
                        "provider": "TMDB",
                        "content_type": "영화",
                        "moods": ["adventure", "focus", "reward"],
                        "trend_keywords": ["SF영화", "화제작"],
                        "duration_label": "TMDB 인기작",
                        "freshness_boost": 5,
                        "source": "tmdb_trending",
                        "image_url": "https://example.com/tmdb-future-city.jpg",
                        "source_url": "https://example.com/tmdb/future-city",
                        "external_url": "https://example.com/watch/future-city",
                        "stats": {"vote_average": 8.0, "popularity": 180, "release_label": "2026-02-20"},
                    },
                    {
                        "id": "tmdb:movie:webtoon-out",
                        "name": "웹툰 파일럿",
                        "description": "테스트용 비지원 웹툰 데이터입니다.",
                        "genres": ["판타지"],
                        "platforms": ["웹툰"],
                        "provider": "네이버웹툰",
                        "content_type": "웹툰",
                        "moods": ["light"],
                        "trend_keywords": ["웹툰"],
                        "duration_label": "회차당 10분",
                        "freshness_boost": 3,
                        "source": "tmdb_trending",
                        "image_url": "https://example.com/webtoon.jpg",
                        "source_url": "https://example.com/webtoon",
                    },
                ],
            }
        },
        upsert=True,
    )

    collection.update_one(
        {"cache_key": "tmdb_trending_tv"},
        {
            "$set": {
                "cache_key": "tmdb_trending_tv",
                "generated_at": now,
                "source_url": "https://example.com/tmdb-tv",
                "items": [
                    {
                        "id": "tmdb:tv:signal-night",
                        "name": "시그널 나이트",
                        "description": "몰입감 높은 범죄 추리 시리즈입니다.",
                        "genres": ["범죄", "미스터리"],
                        "platforms": ["드라마"],
                        "provider": "TMDB",
                        "content_type": "시리즈",
                        "moods": ["focus", "dark", "reward"],
                        "trend_keywords": ["범죄스릴러", "시리즈"],
                        "duration_label": "TMDB 인기 시리즈",
                        "freshness_boost": 4,
                        "source": "tmdb_trending",
                        "image_url": "https://example.com/signal-night.jpg",
                        "source_url": "https://example.com/tmdb/signal-night",
                        "external_url": "https://example.com/watch/signal-night",
                        "stats": {"vote_average": 8.4, "popularity": 160, "release_label": "2026-01-15"},
                    },
                    {
                        "id": "tmdb:tv:youtube-out",
                        "name": "브이로그 셀렉션",
                        "description": "비지원 유튜브 포맷 테스트 데이터입니다.",
                        "genres": ["브이로그"],
                        "platforms": ["유튜브"],
                        "provider": "YouTube",
                        "content_type": "영상",
                        "moods": ["light"],
                        "trend_keywords": ["유튜브"],
                        "duration_label": "20분",
                        "freshness_boost": 3,
                        "source": "tmdb_trending",
                        "image_url": "https://example.com/youtube.jpg",
                        "source_url": "https://example.com/youtube",
                    },
                ],
            }
        },
        upsert=True,
    )


def reset_database():
    with TEST_APP.app_context():
        db = get_db()
        for name in db.list_collection_names():
            db.drop_collection(name)
        mongo.ensure_indexes()
        ensure_runtime_seed()
        seed_content_source_cache()


def create_test_user(name="테스터", email=None, password="secret123"):
    email = email or f"{uuid4().hex[:8]}@example.com"
    user = create_user(name, email, password)
    ensure_profile(user["id"])
    return user


def login_test_user(client, user_id):
    with client.session_transaction() as session:
        session["user_id"] = user_id
