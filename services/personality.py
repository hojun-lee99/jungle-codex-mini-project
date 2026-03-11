from copy import deepcopy


TRAIT_META = {
    "novelty": {"label": "새로움 추구", "description": "낯선 조합과 새로운 장면에 끌리는 정도"},
    "comfort": {"label": "안정 지향", "description": "익숙함과 정서적 안정감을 중시하는 정도"},
    "social": {"label": "관계 에너지", "description": "사람과 함께할 때 동력이 커지는 정도"},
    "aesthetic": {"label": "감각 민감도", "description": "색감, 분위기, 질감, 무드에 반응하는 정도"},
    "focus": {"label": "구조 선호", "description": "일정, 정돈감, 효율, 방향성을 선호하는 정도"},
    "depth": {"label": "정서 해석력", "description": "감정선과 내면 서사에 몰입하는 정도"},
    "energy": {"label": "행동 추진력", "description": "움직임과 활동 강도를 받아들이는 정도"},
    "boldness": {"label": "강한 자극 수용", "description": "강렬한 맛, 분위기, 선택을 즐기는 정도"},
}

LIKERT_OPTIONS = [
    {"value": 1, "label": "전혀 아니다"},
    {"value": 2, "label": "거의 아니다"},
    {"value": 3, "label": "보통이다"},
    {"value": 4, "label": "꽤 그렇다"},
    {"value": 5, "label": "매우 그렇다"},
]

MBTI_TYPES = [
    "INTJ", "INTP", "ENTJ", "ENTP",
    "INFJ", "INFP", "ENFJ", "ENFP",
    "ISTJ", "ISFJ", "ESTJ", "ESFJ",
    "ISTP", "ISFP", "ESTP", "ESFP",
]

SURVEY_QUESTIONS = [
    {
        "id": "unplanned_evening",
        "title": "예상 밖의 여백",
        "statement": "갑작스럽게 비는 저녁이 생기면, 익숙한 루틴보다 아직 경험해보지 못한 장면이 나를 더 빠르게 깨운다.",
        "weights": {"novelty": 1.2, "energy": 0.6, "comfort": -0.7, "focus": -0.3},
    },
    {
        "id": "sensory_memory",
        "title": "감각의 기억 방식",
        "statement": "어떤 공간이나 사람을 떠올릴 때 사실보다 조도, 질감, 공기의 온도 같은 분위기가 먼저 기억에 남는다.",
        "weights": {"aesthetic": 1.3, "depth": 0.7},
    },
    {
        "id": "taste_identity",
        "title": "선택의 정체성",
        "statement": "먹는 것, 입는 것, 보는 것은 단순한 소비보다 지금의 나를 표현하는 언어에 가깝다고 느낀다.",
        "weights": {"aesthetic": 1.0, "depth": 0.8, "boldness": 0.4},
    },
    {
        "id": "emotional_subtext",
        "title": "감정의 결 추적",
        "statement": "콘텐츠나 대화를 마주할 때 사건 그 자체보다 감정의 결, 숨은 의도, 여운을 오래 추적하는 편이다.",
        "weights": {"depth": 1.3, "comfort": 0.4},
    },
    {
        "id": "structure_recovery",
        "title": "회복의 방식",
        "statement": "하루가 흐트러질수록 나를 다시 세우는 것은 강한 자극보다 정돈된 루틴과 예측 가능한 구조다.",
        "weights": {"focus": 1.2, "comfort": 1.0, "novelty": -0.6},
    },
    {
        "id": "solitude_value",
        "title": "혼자만의 시간",
        "statement": "혼자 있는 시간은 비어 있는 시간이 아니라, 내 감각과 생각을 다시 배열하는 핵심 장치에 가깝다.",
        "weights": {"depth": 0.9, "comfort": 0.5, "social": -0.8},
    },
    {
        "id": "social_temperature",
        "title": "관계의 온도",
        "statement": "같은 장소라도 누구와 어떤 에너지로 함께하느냐에 따라 만족도의 크기가 크게 달라진다.",
        "weights": {"social": 1.2, "depth": 0.4},
    },
    {
        "id": "distinctive_choice",
        "title": "무난함보다 결이 있는 선택",
        "statement": "선택이 어려울수록 평균적인 무난함보다 분명한 결이나 캐릭터가 느껴지는 쪽으로 기운다.",
        "weights": {"boldness": 1.1, "novelty": 0.8, "comfort": -0.4},
    },
    {
        "id": "stimulus_release",
        "title": "강한 자극의 해방감",
        "statement": "강한 맛이나 강렬한 분위기, 낯선 조합은 피로보다 해방감으로 다가오는 경우가 더 많다.",
        "weights": {"boldness": 1.2, "energy": 0.8, "novelty": 0.6},
    },
    {
        "id": "narrative_rest",
        "title": "휴식의 정의",
        "statement": "휴식은 단순히 멈추는 상태보다 나를 다른 시야로 데려가는 경험일 때 더 충전된다고 느낀다.",
        "weights": {"novelty": 0.9, "energy": 0.6, "depth": 0.4},
    },
    {
        "id": "flow_consistency",
        "title": "전체 흐름 감각",
        "statement": "무언가를 고를 때 순간의 끌림도 중요하지만, 하루 전체의 흐름과 자연스럽게 이어지는지가 더 중요하다.",
        "weights": {"focus": 1.0, "comfort": 0.7, "boldness": -0.3},
    },
    {
        "id": "micro_meaning",
        "title": "작은 선택의 의미",
        "statement": "사소한 선택에도 나만의 의미나 서사가 있어야 만족감이 길게 남는다.",
        "weights": {"depth": 0.9, "aesthetic": 0.8, "comfort": 0.3},
    },
]

MBTI_LETTER_EFFECTS = {
    "E": {"social": 14, "energy": 8, "novelty": 4},
    "I": {"depth": 10, "comfort": 5, "social": -10},
    "N": {"novelty": 12, "depth": 6, "boldness": 4},
    "S": {"comfort": 10, "focus": 8, "aesthetic": 2},
    "T": {"focus": 10, "boldness": 4, "depth": -4},
    "F": {"depth": 12, "comfort": 6, "aesthetic": 5},
    "J": {"focus": 12, "comfort": 8, "energy": -2},
    "P": {"novelty": 12, "energy": 6, "focus": -4},
}

ITEM_PERSONA_TAGS = {
    "food": {
        "불고기 덮밥": ["comfort", "focus", "social"],
        "마라 크림 파스타": ["novelty", "boldness", "energy", "aesthetic"],
        "연어 포케볼": ["focus", "aesthetic", "energy"],
        "김치찌개 정식": ["comfort", "boldness", "social"],
        "계란볶음밥": ["focus", "comfort"],
        "떡볶이 플래터": ["social", "boldness", "energy"],
        "닭가슴살 또띠아랩": ["focus", "energy"],
        "버섯 된장 파스타": ["depth", "aesthetic", "comfort", "novelty"],
    },
    "fashion": {
        "미니멀 셋업 룩": ["focus", "aesthetic", "comfort"],
        "크림 니트 레이어드": ["comfort", "aesthetic", "depth"],
        "스트릿 윈드브레이커": ["novelty", "energy", "boldness"],
        "모노톤 데님 믹스": ["aesthetic", "comfort", "social"],
        "코지 라운지웨어": ["comfort", "depth"],
        "포멀 블레이저 포인트": ["focus", "boldness", "aesthetic"],
        "애슬레저 트레이닝 셋": ["energy", "social", "focus"],
    },
    "content": {
        "한 회 완결형 힐링 웹툰": ["comfort", "depth"],
        "몰입형 범죄 스릴러 영화": ["boldness", "depth", "focus"],
        "20분 생산성 유튜브": ["focus", "energy"],
        "감성 로맨틱 코미디 드라마": ["comfort", "social", "depth"],
        "판타지 세계관 웹툰": ["novelty", "depth"],
        "현장감 있는 여행 브이로그": ["novelty", "aesthetic", "comfort"],
        "짧고 강한 SF 미드": ["novelty", "boldness", "focus"],
        "마음 편한 요리 영화": ["comfort", "aesthetic", "depth"],
    },
    "activity": {
        "카페 저널링": ["depth", "aesthetic", "comfort"],
        "한강 산책 루프": ["energy", "comfort", "social"],
        "집중형 보드게임 나이트": ["social", "focus", "energy"],
        "실내 클라이밍 체험": ["energy", "boldness", "novelty"],
        "동네 전시 산책": ["aesthetic", "novelty", "depth"],
        "홈트 20분 챌린지": ["focus", "energy"],
        "친구와 신상 맛집 탐방": ["social", "novelty", "boldness"],
        "방 정리 + 플레이리스트 업데이트": ["comfort", "aesthetic", "focus"],
    },
}

ARCHETYPE_RULES = [
    (("novelty", "aesthetic"), "감각형 큐레이터"),
    (("comfort", "depth"), "서사형 코지스트"),
    (("focus", "aesthetic"), "정교한 디렉터"),
    (("social", "energy"), "모멘텀 메이커"),
    (("novelty", "depth"), "세계관 탐험가"),
    (("comfort", "social"), "온도형 호스트"),
]


def build_default_personality():
    neutral_answers = {question["id"]: 3 for question in SURVEY_QUESTIONS}
    neutral_scores = {trait: 50 for trait in TRAIT_META}
    return {
        "mbti": "",
        "survey_answers": neutral_answers,
        "trait_scores": neutral_scores,
        "dominant_traits": [],
        "archetype": "미분석",
        "insights": [
            "MBTI와 심리형 설문을 완료하면 추천 엔진이 자동으로 취향 편향을 반영합니다."
        ],
        "auto_preferences": {
            "food": "심리 분석을 완료하면 음식 취향 문장이 생성됩니다.",
            "fashion": "심리 분석을 완료하면 패션 선호 문장이 생성됩니다.",
            "content": "심리 분석을 완료하면 콘텐츠 선호 문장이 생성됩니다.",
            "activity": "심리 분석을 완료하면 활동 선호 문장이 생성됩니다.",
        },
        "survey_complete": False,
    }


def get_survey_questions():
    return deepcopy(SURVEY_QUESTIONS)


def get_mbti_types():
    return list(MBTI_TYPES)


def get_likert_options():
    return list(LIKERT_OPTIONS)


def _clamp_score(value):
    return max(0, min(100, int(round(value))))


def _top_traits(scores, limit=3):
    sorted_traits = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    return [trait for trait, score in sorted_traits[:limit] if score >= 55]


def _infer_archetype(scores):
    ranked = _top_traits(scores, limit=4)
    ranked_set = set(ranked)
    for required, label in ARCHETYPE_RULES:
        if set(required).issubset(ranked_set):
            return label
    if ranked:
        return f"{TRAIT_META[ranked[0]]['label']} 중심형"
    return "균형형 관찰자"


def _insight_line(scores, high_trait, low_trait):
    high_label = TRAIT_META[high_trait]["label"]
    low_label = TRAIT_META[low_trait]["label"]
    if scores[high_trait] >= 65 and scores[low_trait] <= 45:
        return f"{high_label} 성향이 강하고 {low_label} 축은 비교적 절제되어 있습니다."
    return None


def _build_auto_preferences(scores):
    food = "강한 개성과 새로운 조합이 살아 있는 메뉴" if scores["novelty"] >= 60 or scores["boldness"] >= 60 else "따뜻하고 안정적인 집밥형 메뉴"
    fashion = "톤과 실루엣이 정교하게 정리된 스타일" if scores["focus"] >= 60 else "포인트가 살아 있는 감각형 스타일"
    content = "감정선과 메시지가 오래 남는 서사형 콘텐츠" if scores["depth"] >= 60 else "속도감 있고 몰입이 빠른 콘텐츠"
    activity = "혼자 몰입하거나 분위기를 정리하는 활동" if scores["social"] <= 45 else "사람과 에너지를 주고받는 활동"
    return {
        "food": food,
        "fashion": fashion,
        "content": content,
        "activity": activity,
    }


def _build_insights(mbti, scores, archetype):
    insights = []
    if mbti:
        insights.append(f"MBTI {mbti} 기준으로 {archetype} 성향이 두드러집니다.")

    dominant = _top_traits(scores, limit=3)
    if dominant:
        dominant_labels = ", ".join(TRAIT_META[trait]["label"] for trait in dominant)
        insights.append(f"핵심 축은 {dominant_labels}이며, 일상의 선택에서도 이 성향이 반복됩니다.")

    for high_trait, low_trait in [("novelty", "comfort"), ("social", "depth"), ("focus", "boldness")]:
        line = _insight_line(scores, high_trait, low_trait)
        if line:
            insights.append(line)
            break

    if scores["aesthetic"] >= 60:
        insights.append("시각적 톤과 분위기 일관성이 만족도에 큰 영향을 줍니다.")
    elif scores["comfort"] >= 60:
        insights.append("과한 자극보다 정서적 안정감과 익숙한 흐름이 추천 만족도를 높입니다.")
    else:
        insights.append("상황에 따라 무드와 자극 강도를 유연하게 조정하는 편입니다.")

    return insights[:4]


def extract_survey_answers(form_data):
    answers = {}
    for question in SURVEY_QUESTIONS:
        raw_value = form_data.get(question["id"])
        try:
            answers[question["id"]] = int(raw_value)
        except (TypeError, ValueError):
            answers[question["id"]] = 3
    return answers


def analyze_personality(mbti, answers):
    mbti = (mbti or "").strip().upper()
    scores = {trait: 50.0 for trait in TRAIT_META}

    for question in SURVEY_QUESTIONS:
        answer = int(answers.get(question["id"], 3))
        delta = answer - 3
        for trait, weight in question["weights"].items():
            scores[trait] += delta * weight * 9

    for letter in mbti:
        for trait, bonus in MBTI_LETTER_EFFECTS.get(letter, {}).items():
            scores[trait] += bonus

    normalized_scores = {trait: _clamp_score(value) for trait, value in scores.items()}
    dominant_traits = _top_traits(normalized_scores, limit=3)
    archetype = _infer_archetype(normalized_scores)
    insights = _build_insights(mbti, normalized_scores, archetype)

    survey_complete = bool(mbti and answers)

    return {
        "mbti": mbti,
        "survey_answers": answers,
        "trait_scores": normalized_scores,
        "dominant_traits": dominant_traits,
        "archetype": archetype,
        "insights": insights,
        "auto_preferences": _build_auto_preferences(normalized_scores),
        "survey_complete": survey_complete,
    }


def apply_personality_defaults(personality):
    base = build_default_personality()
    if not personality:
        return base

    merged = deepcopy(base)
    merged.update(personality)
    merged["survey_answers"] = {**base["survey_answers"], **personality.get("survey_answers", {})}
    merged["trait_scores"] = {**base["trait_scores"], **personality.get("trait_scores", {})}
    merged["auto_preferences"] = {**base["auto_preferences"], **personality.get("auto_preferences", {})}
    return merged


def get_persona_tags(category, item_name):
    return ITEM_PERSONA_TAGS.get(category, {}).get(item_name, [])


def personality_bias_for_item(profile, category, item_name):
    personality = apply_personality_defaults((profile or {}).get("personality"))
    scores = personality.get("trait_scores", {})
    tags = get_persona_tags(category, item_name)

    if not tags:
        return 0, None

    bonus = 0
    matched_traits = []
    for trait in tags:
        score = scores.get(trait, 50)
        if score >= 68:
            bonus += 8
            matched_traits.append(TRAIT_META[trait]["label"])
        elif score >= 58:
            bonus += 4
            matched_traits.append(TRAIT_META[trait]["label"])

    if not matched_traits:
        return 0, None

    matched_traits = matched_traits[:2]
    reason = f"MBTI/심리 분석상 {' · '.join(matched_traits)} 성향과 어울림"
    return bonus, reason
