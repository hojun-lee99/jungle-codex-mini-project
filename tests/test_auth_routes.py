import unittest

from db.mongo import get_collection

from tests.test_support import TEST_APP, create_test_user, reset_database


class AuthRouteTests(unittest.TestCase):
    def setUp(self):
        reset_database()
        self.app = TEST_APP
        self.client = self.app.test_client()

    def test_index_page_shows_new_service_name(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("WhatShouldIDo", response.get_data(as_text=True))

    def test_dashboard_requires_login(self):
        response = self.client.get("/dashboard")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.location)
        self.assertIn("next=/dashboard", response.location)

    def test_register_success_creates_user_and_profile(self):
        response = self.client.post(
            "/register",
            data={
                "name": "홍길동",
                "email": "hong@example.com",
                "password": "secret123",
                "password_confirm": "secret123",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/dashboard", response.location)
        with self.app.app_context():
            self.assertEqual(get_collection("users").count_documents({}), 1)
            self.assertEqual(get_collection("profiles").count_documents({}), 1)

    def test_register_duplicate_email_returns_error(self):
        with self.app.app_context():
            create_test_user(email="dup@example.com")

        response = self.client.post(
            "/register",
            data={
                "name": "다른 사용자",
                "email": "dup@example.com",
                "password": "secret123",
                "password_confirm": "secret123",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("이미 사용 중인 이메일입니다.", response.get_data(as_text=True))

    def test_login_invalid_password_shows_error(self):
        with self.app.app_context():
            create_test_user(email="login@example.com", password="secret123")

        response = self.client.post(
            "/login",
            data={"email": "login@example.com", "password": "wrong-password"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("이메일 또는 비밀번호를 다시 확인해주세요.", response.get_data(as_text=True))

    def test_logout_clears_session(self):
        with self.app.app_context():
            user = create_test_user()

        with self.client.session_transaction() as session:
            session["user_id"] = user["id"]

        response = self.client.get("/logout")

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/"))
        with self.client.session_transaction() as session:
            self.assertNotIn("user_id", session)


if __name__ == "__main__":
    unittest.main()
