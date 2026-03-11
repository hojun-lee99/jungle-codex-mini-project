from copy import deepcopy

from services.catalog import ACTIVITY_CATALOG, CONTENT_CATALOG, FASHION_CATALOG, FOOD_CATALOG
from services.personality import personality_bias_for_item
from utils import get_time_slot


def _normalize(values):
    return {value.strip().lower() for value in values if value}


def _recent_names(history_entries, category):
    names = set()
    for entry in history_entries or []:
        if entry["category"] == category:
            names.add(entry["recommendation"]["name"].strip().lower())
    return names


def _trend_keywords(trends, category=None):
    keywords = []
    for trend in trends or []:
        if category and trend["category"] != category:
            continue
        keywords.append(trend["keyword"].strip().lower())
    return set(keywords)


def _finalize_result(category, form_input, candidates):
    ranked = sorted(candidates, key=lambda item: item["score"], reverse=True)
    top_pick = ranked[0]
    top_pick["reason_text"] = " / ".join(top_pick["reasons"][:3])
    for candidate in ranked[1:3]:
        candidate["reason_text"] = " / ".join(candidate["reasons"][:2])

    return {
        "category": category,
        "request_snapshot": form_input,
        "top_pick": top_pick,
        "alternatives": ranked[1:3],
    }


def _apply_personality_bias(profile, category, item_name, reasons):
    bonus, reason = personality_bias_for_item(profile, category, item_name)
    if reason:
        reasons.append(reason)
    return bonus


def recommend_food(profile, form_input, trends=None, recent_history=None):
    favorites = _normalize(profile["food"].get("favorites", []))
    dislikes = _normalize(profile["food"].get("dislikes", []))
    ingredients = _normalize(form_input.get("ingredients") or profile["food"].get("available_ingredients", []))
    trend_keywords = _trend_keywords(trends, "food")
    recent_names = _recent_names(recent_history, "food")

    mood = form_input.get("mood", "comfort")
    time_slot = form_input.get("time_slot") or get_time_slot()
    spicy_pref = form_input.get("spicy", profile["food"].get("spice", "any"))

    candidates = []
    for item in FOOD_CATALOG:
        score = 45
        reasons = []
        item_tokens = _normalize(item["tags"] + item["ingredients"] + item["trend_keywords"])

        matched_preferences = favorites & item_tokens
        if matched_preferences:
            score += min(len(matched_preferences) * 12, 24)
            reasons.append(f"취향 일치 {', '.join(sorted(matched_preferences)[:2])}")

        blocked_tokens = dislikes & item_tokens
        if blocked_tokens:
            score -= len(blocked_tokens) * 15
            reasons.append("기피 재료와 일부 충돌")

        if time_slot in item["meal_times"]:
            score += 16
            reasons.append("현재 시간대에 잘 맞음")

        if mood in item["moods"]:
            score += 10
            reasons.append("지금 기분에 어울림")

        if spicy_pref == "yes" and item["spicy"] == "spicy":
            score += 10
            reasons.append("매운맛 선호 반영")
        elif spicy_pref == "no" and item["spicy"] == "mild":
            score += 8
            reasons.append("맵지 않은 메뉴")
        elif spicy_pref == "any":
            score += 3

        ingredient_overlap = ingredients & _normalize(item["ingredients"])
        if ingredient_overlap:
            score += min(len(ingredient_overlap) * 7, 21)
            reasons.append(f"보유 재료 활용 {', '.join(sorted(ingredient_overlap)[:2])}")

        trend_hits = trend_keywords & _normalize(item["trend_keywords"])
        if trend_hits:
            score += min(len(trend_hits) * 6, 12)
            reasons.append("트렌드 키워드 가중치")

        if item["name"].strip().lower() in recent_names:
            score -= 12
            reasons.append("최근 추천 중복 보정")

        score += _apply_personality_bias(profile, "food", item["name"], reasons)

        candidates.append(
            {
                "name": item["name"],
                "description": item["description"],
                "score": score,
                "reasons": reasons or ["기본 점수가 안정적인 메뉴"],
                "meta": [time_slot, item["spicy"], ", ".join(item["ingredients"][:3])],
            }
        )

    return _finalize_result(
        "food",
        {
            "mood": mood,
            "time_slot": time_slot,
            "spicy": spicy_pref,
            "ingredients": list(ingredients),
        },
        candidates,
    )


def recommend_fashion(profile, form_input, trends=None, recent_history=None):
    styles = _normalize(form_input.get("styles") or profile["fashion"].get("styles", []))
    colors = _normalize(form_input.get("colors") or profile["fashion"].get("colors", []))
    personal_color = form_input.get("personal_color") or profile["fashion"].get("personal_color", "spring warm")
    temperature = int(form_input.get("temperature") or 20)
    condition = form_input.get("condition", "clear")
    trend_keywords = _trend_keywords(trends, "fashion")
    recent_names = _recent_names(recent_history, "fashion")

    candidates = []
    for item in FASHION_CATALOG:
        score = 40
        reasons = []

        style_hits = styles & _normalize(item["styles"])
        if style_hits:
            score += min(len(style_hits) * 13, 26)
            reasons.append(f"스타일 취향 {', '.join(sorted(style_hits)[:2])}")

        color_hits = colors & _normalize(item["colors"])
        if color_hits:
            score += min(len(color_hits) * 9, 18)
            reasons.append(f"선호 컬러 {', '.join(sorted(color_hits)[:2])}")

        if personal_color in item["personal_colors"]:
            score += 12
            reasons.append("퍼스널 컬러 조화")

        if item["temp_min"] <= temperature <= item["temp_max"]:
            score += 18
            reasons.append("현재 온도에 적합")
        else:
            score -= 10

        if condition in item["conditions"]:
            score += 8
            reasons.append("날씨 상황 반영")

        trend_hits = trend_keywords & _normalize(item["trend_keywords"])
        if trend_hits:
            score += min(len(trend_hits) * 6, 12)
            reasons.append("트렌드 스타일 반영")

        if item["name"].strip().lower() in recent_names:
            score -= 10
            reasons.append("최근 코디와 겹치지 않게 조정")

        score += _apply_personality_bias(profile, "fashion", item["name"], reasons)

        candidates.append(
            {
                "name": item["name"],
                "description": item["description"],
                "score": score,
                "reasons": reasons or ["무난한 데일리 코디"],
                "meta": [f"{item['temp_min']}~{item['temp_max']}°C", personal_color, condition],
            }
        )

    return _finalize_result(
        "fashion",
        {
            "styles": list(styles),
            "colors": list(colors),
            "personal_color": personal_color,
            "temperature": temperature,
            "condition": condition,
        },
        candidates,
    )


def recommend_content(profile, form_input, trends=None, recent_history=None):
    genres = _normalize(form_input.get("genres") or profile["content"].get("genres", []))
    platforms = _normalize(form_input.get("platforms") or profile["content"].get("platforms", []))
    mood = form_input.get("mood", "light")
    trend_keywords = _trend_keywords(trends, "content")
    recent_names = _recent_names(recent_history, "content")

    candidates = []
    for item in CONTENT_CATALOG:
        score = 42
        reasons = []

        genre_hits = genres & _normalize(item["genres"])
        if genre_hits:
            score += min(len(genre_hits) * 12, 24)
            reasons.append(f"장르 취향 {', '.join(sorted(genre_hits)[:2])}")

        platform_hits = platforms & _normalize(item["platforms"])
        if platform_hits:
            score += min(len(platform_hits) * 10, 20)
            reasons.append(f"선호 플랫폼 {', '.join(sorted(platform_hits)[:2])}")

        if mood in item["moods"]:
            score += 10
            reasons.append("현재 무드와 맞음")

        trend_hits = trend_keywords & _normalize(item["trend_keywords"])
        if trend_hits:
            score += min(len(trend_hits) * 6, 12)
            reasons.append("지금 뜨는 키워드 반영")

        if item["name"].strip().lower() in recent_names:
            score -= 10
            reasons.append("최근 추천 중복 보정")

        score += _apply_personality_bias(profile, "content", item["name"], reasons)

        candidates.append(
            {
                "name": item["name"],
                "description": item["description"],
                "score": score,
                "reasons": reasons or ["무난하게 만족도 높은 콘텐츠"],
                "meta": [", ".join(item["platforms"]), ", ".join(item["genres"][:2]), mood],
            }
        )

    return _finalize_result(
        "content",
        {
            "genres": list(genres),
            "platforms": list(platforms),
            "mood": mood,
        },
        candidates,
    )


def recommend_activity(profile, form_input, weather, trends=None, recent_history=None):
    preferred_space = form_input.get("indoor_outdoor") or profile["activity"].get("indoor_outdoor", "mixed")
    energy = form_input.get("energy") or profile["activity"].get("energy", "medium")
    social = form_input.get("social") or profile["activity"].get("social", "either")
    budget = form_input.get("budget") or profile["activity"].get("budget", "medium")
    trend_keywords = _trend_keywords(trends, "activity")
    recent_names = _recent_names(recent_history, "activity")

    candidates = []
    for item in ACTIVITY_CATALOG:
        score = 40
        reasons = []

        if preferred_space in {item["indoor_outdoor"], "mixed"} or item["indoor_outdoor"] == "mixed":
            score += 13
            reasons.append("실내외 조건 일치")

        if energy == item["energy"]:
            score += 12
            reasons.append("현재 에너지 레벨과 맞음")

        if social in {item["social"], "either"} or item["social"] == "either":
            score += 10
            reasons.append("함께/혼자 조건 반영")

        if budget == item["budget"]:
            score += 9
            reasons.append("예산 범위와 비슷함")

        if weather["condition"] == "rainy" and item["indoor_outdoor"] == "outdoor":
            score -= 14
            reasons.append("비 오는 날 보정")
        elif weather["condition"] == "clear" and item["indoor_outdoor"] == "outdoor":
            score += 8
            reasons.append("야외 활동하기 좋은 날씨")

        trend_hits = trend_keywords & _normalize(item["trend_keywords"])
        if trend_hits:
            score += min(len(trend_hits) * 6, 12)
            reasons.append("최근 트렌드 반영")

        if item["name"].strip().lower() in recent_names:
            score -= 10
            reasons.append("최근 활동 추천과 겹치지 않게 조정")

        score += _apply_personality_bias(profile, "activity", item["name"], reasons)

        candidates.append(
            {
                "name": item["name"],
                "description": item["description"],
                "score": score,
                "reasons": reasons or ["기본 만족도가 높은 활동"],
                "meta": [item["indoor_outdoor"], item["energy"], weather["condition"]],
            }
        )

    return _finalize_result(
        "activity",
        {
            "indoor_outdoor": preferred_space,
            "energy": energy,
            "social": social,
            "budget": budget,
            "weather_condition": weather["condition"],
        },
        candidates,
    )


def build_dashboard_bundle(profile, weather, trends, recent_history):
    content_profile = deepcopy(profile["content"])
    food_result = recommend_food(
        profile,
        {
            "mood": "comfort",
            "time_slot": get_time_slot(),
            "spicy": profile["food"].get("spice", "any"),
            "ingredients": profile["food"].get("available_ingredients", []),
        },
        trends=trends,
        recent_history=recent_history,
    )
    fashion_result = recommend_fashion(
        profile,
        {
            "styles": profile["fashion"].get("styles", []),
            "colors": profile["fashion"].get("colors", []),
            "personal_color": profile["fashion"].get("personal_color", "spring warm"),
            "temperature": weather["temperature"],
            "condition": weather["condition"],
        },
        trends=trends,
        recent_history=recent_history,
    )
    content_result = recommend_content(
        profile,
        {
            "genres": content_profile.get("genres", []),
            "platforms": content_profile.get("platforms", []),
            "mood": "light",
        },
        trends=trends,
        recent_history=recent_history,
    )
    activity_result = recommend_activity(
        profile,
        {
            "indoor_outdoor": profile["activity"].get("indoor_outdoor", "mixed"),
            "energy": profile["activity"].get("energy", "medium"),
            "social": profile["activity"].get("social", "either"),
            "budget": profile["activity"].get("budget", "medium"),
        },
        weather=weather,
        trends=trends,
        recent_history=recent_history,
    )
    return {
        "food": food_result,
        "fashion": fashion_result,
        "content": content_result,
        "activity": activity_result,
    }
