from copy import deepcopy
from uuid import uuid4

from bson import ObjectId
from pymongo import DESCENDING, MongoClient


class MongoRepository:
    def __init__(self, mongo_uri, db_name):
        self.mode = "memory"
        self._memory_store = []
        self.client = None
        self.collection = None

        try:
            self.client = MongoClient(mongo_uri, serverSelectionTimeoutMS=1500)
            self.client.admin.command("ping")
            self.collection = self.client[db_name]["documents"]
            self.mode = "mongo"
        except Exception:
            self.client = None
            self.collection = None
            self.mode = "memory"

    def create_document(self, payload):
        if self.mode == "mongo":
            result = self.collection.insert_one(payload)
            return str(result.inserted_id)

        document = deepcopy(payload)
        document["id"] = uuid4().hex
        self._memory_store.append(document)
        return document["id"]

    def list_documents(self, limit=100):
        if self.mode == "mongo":
            cursor = self.collection.find().sort("uploaded_at", DESCENDING).limit(limit)
            return [self._serialize(document) for document in cursor]

        documents = sorted(
            self._memory_store,
            key=lambda item: item.get("uploaded_at"),
            reverse=True,
        )
        return [deepcopy(document) for document in documents[:limit]]

    def get_document(self, document_id):
        if self.mode == "mongo":
            try:
                document = self.collection.find_one({"_id": ObjectId(document_id)})
            except Exception:
                return None
            return self._serialize(document) if document else None

        for document in self._memory_store:
            if document.get("id") == document_id:
                return deepcopy(document)
        return None

    def _serialize(self, document):
        if not document:
            return None
        serialized = deepcopy(document)
        serialized["id"] = str(serialized.pop("_id"))
        return serialized

