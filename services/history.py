from datetime import date, datetime

from db.mongo import get_collection


CATEGORY_LABELS = {
    "food": "음식",
    "fashion": "패션",
    "content": "콘텐츠",
    "activity": "활동",
}


def _serialize_history(history_doc):
    entry = dict(history_doc)
    entry["id"] = str(entry["_id"])
    entry["created_label"] = entry["created_at"].strftime("%m.%d %H:%M")
    entry["category_label"] = CATEGORY_LABELS.get(entry["category"], entry["category"])
    return entry


def save_recommendation(user_id, category, request_snapshot, top_pick, alternatives, context="manual", day_key=None):
    history_doc = {
        "user_id": user_id,
        "category": category,
        "request_snapshot": request_snapshot,
        "recommendation": top_pick,
        "alternatives": alternatives,
        "context": context,
        "day_key": day_key,
        "created_at": datetime.utcnow(),
    }
    get_collection("recommendation_history").insert_one(history_doc)


def get_recent_history(user_id, limit=5):
    cursor = (
        get_collection("recommendation_history")
        .find({"user_id": user_id})
        .sort("created_at", -1)
        .limit(limit)
    )
    return [_serialize_history(item) for item in cursor]


def ensure_dashboard_daily_history(user_id, recommendation_bundle):
    today_key = date.today().isoformat()
    history = get_collection("recommendation_history")
    already_exists = history.count_documents(
        {"user_id": user_id, "context": "dashboard-daily", "day_key": today_key},
        limit=1,
    )
    if already_exists:
        return

    for category, result in recommendation_bundle.items():
        save_recommendation(
            user_id=user_id,
            category=category,
            request_snapshot=result["request_snapshot"],
            top_pick=result["top_pick"],
            alternatives=result["alternatives"],
            context="dashboard-daily",
            day_key=today_key,
        )


def get_full_history(user_id, limit=30):
    cursor = (
        get_collection("recommendation_history")
        .find({"user_id": user_id})
        .sort("created_at", -1)
        .limit(limit)
    )
    return [_serialize_history(item) for item in cursor]
