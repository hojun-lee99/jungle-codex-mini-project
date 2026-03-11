from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from app.utils import allowed_file


class DocumentProcessingService:
    def __init__(
        self,
        repository,
        ocr_service,
        parser,
        rule_engine,
        upload_folder,
        allowed_extensions,
        auto_delete_original=False,
    ):
        self.repository = repository
        self.ocr_service = ocr_service
        self.parser = parser
        self.rule_engine = rule_engine
        self.upload_folder = Path(upload_folder)
        self.allowed_extensions = allowed_extensions
        self.auto_delete_original = auto_delete_original

    def process_upload(self, file_storage: FileStorage):
        if not allowed_file(file_storage.filename, self.allowed_extensions):
            allowed = ", ".join(sorted(self.allowed_extensions))
            raise ValueError(f"지원하지 않는 파일 형식입니다. 허용 형식: {allowed}")

        saved_path, original_filename = self._save_file(file_storage)
        extracted_text = self.ocr_service.extract_text(saved_path)
        parsed_data = self.parser.parse(extracted_text)
        validation = self.rule_engine.validate(parsed_data)

        record = {
            "original_filename": original_filename,
            "stored_filename": saved_path.name,
            "file_extension": saved_path.suffix.lower().replace(".", ""),
            "uploaded_at": datetime.now(timezone.utc),
            "status": validation["status"],
            "confidence": validation["confidence"],
            "reason": validation["reason"],
            "validation": validation,
            "parsed_data": parsed_data,
            "extracted_text": extracted_text,
            "privacy_mode": self.auto_delete_original,
            "preview_available": True,
        }

        if self.auto_delete_original:
            if saved_path.exists():
                saved_path.unlink()
            record["stored_filename"] = None
            record["preview_available"] = False
            record["extracted_text"] = None

        document_id = self.repository.create_document(record)
        return self.repository.get_document(document_id)

    def _save_file(self, file_storage: FileStorage):
        original_filename = secure_filename(file_storage.filename)
        extension = Path(original_filename).suffix.lower()
        stored_name = f"{uuid4().hex}{extension}"
        saved_path = self.upload_folder / stored_name
        file_storage.save(saved_path)
        return saved_path, original_filename

