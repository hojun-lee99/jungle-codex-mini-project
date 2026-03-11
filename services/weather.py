from datetime import datetime


SEASONAL_WEATHER = {
    1: {"temperature": 1, "condition": "clear", "label": "차가운 겨울 공기"},
    2: {"temperature": 4, "condition": "windy", "label": "바람이 있는 늦겨울"},
    3: {"temperature": 12, "condition": "cloudy", "label": "가벼운 봄바람"},
    4: {"temperature": 17, "condition": "clear", "label": "산뜻한 봄날"},
    5: {"temperature": 22, "condition": "clear", "label": "초여름 햇살"},
    6: {"temperature": 24, "condition": "rainy", "label": "습한 장마 분위기"},
    7: {"temperature": 29, "condition": "clear", "label": "강한 여름 더위"},
    8: {"temperature": 30, "condition": "rainy", "label": "무더운 한낮"},
    9: {"temperature": 24, "condition": "clear", "label": "산책하기 좋은 초가을"},
    10: {"temperature": 18, "condition": "clear", "label": "선선한 가을 공기"},
    11: {"temperature": 11, "condition": "cloudy", "label": "차분한 늦가을"},
    12: {"temperature": 4, "condition": "windy", "label": "코트가 필요한 초겨울"},
}


def classify_condition(temperature: int):
    if temperature >= 27:
        return "clear"
    if temperature <= 5:
        return "windy"
    return "cloudy"


def get_weather_snapshot(city="Seoul", temperature_override=None, condition_override=None):
    today = datetime.now()
    weather = dict(SEASONAL_WEATHER[today.month])

    if temperature_override not in (None, ""):
        weather["temperature"] = int(temperature_override)
        weather["condition"] = classify_condition(weather["temperature"])
        weather["label"] = "사용자 입력 온도 기준"

    if condition_override:
        weather["condition"] = condition_override

    weather["city"] = city
    return weather
