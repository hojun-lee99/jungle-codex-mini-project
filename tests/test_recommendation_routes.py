import unittest

from werkzeug.datastructures import MultiDict

from db.mongo import get_collection
from services.profile_service import get_profile
from services.trends import build_quiz_board
from tests.test_support import TEST_APP, create_test_user, login_test_user, reset_database


class RecommendationRouteTests(unittest.TestCase):
    def setUp(self):
        reset_database()
        self.app = TEST_APP
        self.client = self.app.test_client()
        with self.app.app_context():
            self.user = create_test_user()
        login_test_user(self.client, self.user["id"])

    def test_profile_page_shows_selectable_content_options_only(self):
        response = self.client.get("/profile")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('value="넷플릭스"', body)
        self.assertIn('value="시리즈"', body)
        self.assertNotIn('value="웹툰"', body)

    def test_profile_post_filters_unsupported_content_preferences(self):
        payload = MultiDict(
            [
                ("food_favorites", "한식, 집밥"),
                ("food_dislikes", "고수"),
                ("food_ingredients", "계란, 양파"),
                ("food_spice", "yes"),
                ("fashion_styles", "캐주얼"),
                ("fashion_colors", "블랙"),
                ("fashion_personal_color", "winter cool"),
                ("content_genres", "액션"),
                ("content_genres", "판타지"),
                ("content_platforms", "넷플릭스"),
                ("content_platforms", "드라마"),
                ("content_platforms", "웹툰"),
                ("activity_indoor_outdoor", "indoor"),
                ("activity_energy", "low"),
                ("activity_social", "solo"),
                ("activity_budget", "medium"),
            ]
        )

        response = self.client.post("/profile", data=payload)

        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            profile = get_profile(self.user["id"])
            self.assertEqual(profile["content"]["genres"], ["액션"])
            self.assertEqual(profile["content"]["platforms"], ["넷플릭스", "시리즈"])

    def test_food_post_saves_history_entry(self):
        response = self.client.post(
            "/food",
            data={
                "favorites": "한식, 집밥",
                "dislikes": "",
                "ingredients": "계란, 양파",
                "mood": "comfort",
                "time_slot": "dinner",
                "spicy": "any",
            },
        )

        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            entries = list(get_collection("recommendation_history").find({"user_id": self.user["id"], "category": "food"}))
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0]["context"], "category-form")

    def test_dashboard_daily_history_is_saved_once(self):
        first_response = self.client.get("/dashboard")
        second_response = self.client.get("/dashboard")

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)
        with self.app.app_context():
            count = get_collection("recommendation_history").count_documents(
                {"user_id": self.user["id"], "context": "dashboard-daily"}
            )
            self.assertEqual(count, 4)

    def test_content_page_loads_seeded_recommendations(self):
        response = self.client.get("/content")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("미드나이트 런", body)
        self.assertIn("서울의 봄", body)

    def test_content_feedback_success_returns_summary(self):
        response = self.client.post(
            "/content/feedback",
            json={"content_id": "netflix:test:midnight-run", "sentiment": "like"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["summary"]["liked_count"], 1)
        self.assertEqual(payload["summary"]["disliked_count"], 0)

    def test_content_feedback_invalid_sentiment_returns_400(self):
        response = self.client.post(
            "/content/feedback",
            json={"content_id": "netflix:test:midnight-run", "sentiment": "maybe"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("유효하지 않은 피드백입니다.", response.get_json()["message"])

    def test_content_feedback_missing_item_returns_404(self):
        response = self.client.post(
            "/content/feedback",
            json={"content_id": "missing-id", "sentiment": "like"},
        )

        self.assertEqual(response.status_code, 404)
        self.assertIn("콘텐츠 정보를 찾을 수 없습니다.", response.get_json()["message"])

    def test_quiz_vote_invalid_choice_returns_400(self):
        response = self.client.post("/quiz/vote", json={"quiz_id": "food_faceoff", "choice": "up"})

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.get_json()["ok"])

    def test_quiz_vote_success_returns_updated_result(self):
        with self.app.app_context():
            quiz_id = build_quiz_board()[0]["id"]

        response = self.client.post("/quiz/vote", json={"quiz_id": quiz_id, "choice": "left"})

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["result"]["quiz_id"], quiz_id)
        self.assertGreaterEqual(payload["result"]["left_votes"], 1)

    def test_history_page_renders_saved_entry(self):
        self.client.post(
            "/food",
            data={
                "favorites": "한식",
                "dislikes": "",
                "ingredients": "",
                "mood": "comfort",
                "time_slot": "lunch",
                "spicy": "no",
            },
        )

        response = self.client.get("/history")

        self.assertEqual(response.status_code, 200)
        self.assertIn("추천 히스토리", response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
