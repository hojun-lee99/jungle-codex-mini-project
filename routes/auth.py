from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from services.account import authenticate_user, create_user
from services.profile_service import ensure_profile


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        next_url = request.form.get("next") or url_for("main.dashboard")

        user = authenticate_user(email, password)
        if not user:
            flash("이메일 또는 비밀번호를 다시 확인해주세요.", "danger")
            return render_template("auth/login.html", next_url=next_url)

        session.clear()
        session["user_id"] = user["id"]
        flash(f"{user['name']}님, 다시 오셨네요.", "success")
        return redirect(next_url)

    return render_template("auth/login.html", next_url=request.args.get("next"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")

        if not name or not email or not password:
            flash("이름, 이메일, 비밀번호를 모두 입력해주세요.", "danger")
            return render_template("auth/register.html")

        if password != password_confirm:
            flash("비밀번호 확인이 일치하지 않습니다.", "danger")
            return render_template("auth/register.html")

        if len(password) < 6:
            flash("비밀번호는 6자 이상으로 설정해주세요.", "danger")
            return render_template("auth/register.html")

        try:
            user = create_user(name, email, password)
            ensure_profile(user["id"])
        except ValueError as exc:
            flash(str(exc), "danger")
            return render_template("auth/register.html")

        session.clear()
        session["user_id"] = user["id"]
        flash("회원가입이 완료되었습니다. 오늘의 추천을 시작해볼까요?", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("auth/register.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("로그아웃되었습니다.", "info")
    return redirect(url_for("main.index"))
