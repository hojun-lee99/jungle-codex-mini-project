from datetime import datetime

from bson import ObjectId
from werkzeug.security import check_password_hash, generate_password_hash

from db.mongo import get_collection


def _serialize_user(user_doc):
    if not user_doc:
        return None
    user = dict(user_doc)
    user["id"] = str(user["_id"])
    return user


def get_user_by_email(email: str):
    return _serialize_user(get_collection("users").find_one({"email": email.strip().lower()}))


def get_user_by_id(user_id: str):
    if not user_id:
        return None
    try:
        user_doc = get_collection("users").find_one({"_id": ObjectId(user_id)})
    except Exception:
        return None
    return _serialize_user(user_doc)


def create_user(name: str, email: str, password: str):
    users = get_collection("users")
    normalized_email = email.strip().lower()
    if users.find_one({"email": normalized_email}):
        raise ValueError("이미 사용 중인 이메일입니다.")

    user_doc = {
        "name": name.strip(),
        "email": normalized_email,
        "password_hash": generate_password_hash(password, method="pbkdf2:sha256"),
        "created_at": datetime.utcnow(),
    }
    inserted = users.insert_one(user_doc)
    user_doc["_id"] = inserted.inserted_id
    return _serialize_user(user_doc)


def authenticate_user(email: str, password: str):
    user_doc = get_collection("users").find_one({"email": email.strip().lower()})
    if not user_doc:
        return None
    if not check_password_hash(user_doc["password_hash"], password):
        return None
    return _serialize_user(user_doc)
