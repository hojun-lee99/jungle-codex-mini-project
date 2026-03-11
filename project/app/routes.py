from pathlib import Path

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)


main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    return render_template(
        "index.html",
        auto_delete=current_app.config["AUTO_DELETE_ORIGINAL"],
        allowed_extensions=sorted(current_app.config["ALLOWED_EXTENSIONS"]),
    )


@main_bp.route("/upload", methods=["POST"])
def upload_document():
    file_storage = request.files.get("document")
    if not file_storage or not file_storage.filename:
        flash("업로드할 문서를 선택해 주세요.", "danger")
        return redirect(url_for("main.index"))

    try:
        document = current_app.extensions["document_service"].process_upload(file_storage)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("main.index"))
    except Exception:
        current_app.logger.exception("문서 처리 실패")
        flash("문서 처리 중 오류가 발생했습니다. 설정과 의존성을 확인해 주세요.", "danger")
        return redirect(url_for("main.index"))

    flash("문서 처리가 완료되었습니다.", "success")
    return redirect(url_for("main.document_detail", document_id=document["id"]))


@main_bp.route("/dashboard")
def dashboard():
    repository = current_app.extensions["repository"]
    documents = repository.list_documents(limit=100)
    summary = {
        "total": len(documents),
        "approved": sum(1 for doc in documents if doc.get("status") == "APPROVED"),
        "review_required": sum(1 for doc in documents if doc.get("status") == "REVIEW_REQUIRED"),
        "privacy_enabled": sum(1 for doc in documents if doc.get("privacy_mode")),
    }
    return render_template(
        "dashboard.html",
        documents=documents,
        summary=summary,
        storage_mode=repository.mode,
    )


@main_bp.route("/documents/<document_id>")
def document_detail(document_id):
    repository = current_app.extensions["repository"]
    document = repository.get_document(document_id)
    if not document:
        abort(404)

    preview_kind = None
    if document.get("preview_available"):
        extension = document.get("file_extension", "").lower()
        if extension in {"png", "jpg", "jpeg"}:
            preview_kind = "image"
        elif extension == "pdf":
            preview_kind = "pdf"

    return render_template(
        "detail.html",
        document=document,
        preview_kind=preview_kind,
    )


@main_bp.route("/uploads/<path:stored_filename>")
def uploaded_file(stored_filename):
    upload_folder = Path(current_app.config["UPLOAD_FOLDER"])
    file_path = upload_folder / stored_filename
    if not file_path.exists():
        abort(404)
    return send_from_directory(str(upload_folder), stored_filename)

