from datetime import datetime

from db.mongo import get_collection


DEFAULT_TRENDS = [
    {"keyword": "헬시플레이트", "category": "food", "score": 96, "headline": "가벼운 점심 트렌드"},
    {"keyword": "마라", "category": "food", "score": 93, "headline": "매운 음식 키워드 급상승"},
    {"keyword": "고프코어", "category": "fashion", "score": 91, "headline": "윈드브레이커 스타일 강세"},
    {"keyword": "오피스코어", "category": "fashion", "score": 84, "headline": "정돈된 셋업 룩 재부상"},
    {"keyword": "힐링웹툰", "category": "content", "score": 88, "headline": "짧고 편한 콘텐츠 인기"},
    {"keyword": "범죄스릴러", "category": "content", "score": 86, "headline": "몰입형 저녁 콘텐츠 수요"},
    {"keyword": "전시회", "category": "activity", "score": 79, "headline": "가벼운 문화생활 탐색 증가"},
    {"keyword": "러닝크루", "category": "activity", "score": 77, "headline": "저녁 야외 활동 관심 상승"},
]

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


def ensure_runtime_seed():
    trends = get_collection("trend_cache")
    if trends.count_documents({}, limit=1) == 0:
        trends.insert_one(
            {
                "source": "sample_google_trends",
                "region": "KR",
                "generated_at": datetime.utcnow(),
                "keywords": DEFAULT_TRENDS,
            }
        )


def get_latest_trends(limit=8):
    ensure_runtime_seed()
    latest = get_collection("trend_cache").find_one(sort=[("generated_at", -1)])
    return (latest or {}).get("keywords", [])[:limit]


def get_trends_by_category():
    grouped = {"food": [], "fashion": [], "content": [], "activity": []}
    for trend in get_latest_trends(limit=20):
        grouped.setdefault(trend["category"], []).append(trend)
    return grouped


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
