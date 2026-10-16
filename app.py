
import os
from pathlib import Path

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_from_directory,
    abort,
    jsonify,
)
from werkzeug.exceptions import RequestEntityTooLarge

from file_service import FileService


app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "change-this-secret-before-deployment"
)
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(
    os.environ.get("FILEFLOW_DATA_DIR", str(BASE_DIR / "storage"))
)

service = FileService(DATA_DIR)


@app.context_processor
def inject_site_info():
    """Shared values available to every HTML template."""
    return {
        "site_name": "Sandhu Drive",
        "upload_limit_mb": 500,
        "current_year": __import__("datetime").datetime.now().year,
    }


@app.errorhandler(RequestEntityTooLarge)
def handle_large_upload(error):
    flash(
        "Upload request is too large. Maximum supported request size is 500 MB.",
        "error",
    )
    return redirect(url_for("index"))


@app.route("/")
def index():
    query = request.args.get("q", "").strip()
    category = request.args.get("type", "all").lower()

    allowed_categories = {
        "all", "image", "document", "audio", "video", "other"
    }
    if category not in allowed_categories:
        category = "all"

    files = service.list_files()

    if query:
        query_folded = query.casefold()
        files = [
            item for item in files
            if query_folded in item["name"].casefold()
        ]

    if category != "all":
        files = [
            item for item in files
            if item["category"].casefold() == category
        ]

    return render_template(
        "index.html",
        files=files,
        stats=service.stats(),
        query=query,
        kind=category,
    )


@app.route("/upload", methods=["POST"])
def upload():
    uploaded_files = request.files.getlist("files")

    if not any(file and file.filename for file in uploaded_files):
        flash("Please select at least one file to upload.", "error")
        return redirect(url_for("index"))

    successful = 0

    for uploaded in uploaded_files:
        if not uploaded or not uploaded.filename:
            continue

        try:
            service.save_upload(uploaded)
            successful += 1
        except ValueError as error:
            flash(f"{uploaded.filename}: {error}", "error")

    if successful:
        flash(f"{successful} file(s) uploaded successfully.", "success")

    return redirect(url_for("index"))


@app.route("/download/<path:name>")
def download(name):
    safe_name = service.resolve_name(name)

    if safe_name is None:
        abort(404)

    return send_from_directory(
        service.root,
        safe_name,
        as_attachment=True,
        download_name=safe_name,
    )


@app.route("/preview/<path:name>")
def preview(name):
    safe_name = service.resolve_name(name)

    if safe_name is None:
        abort(404)

    extension = Path(safe_name).suffix.lower()

    # Avoid rendering active content such as HTML or JavaScript.
    unsafe_extensions = {
        ".html", ".htm", ".svg", ".js", ".mjs",
        ".xml", ".xhtml", ".xht",
    }

    return send_from_directory(
        service.root,
        safe_name,
        as_attachment=extension in unsafe_extensions,
        download_name=safe_name,
    )


@app.route("/rename", methods=["POST"])
def rename():
    old_name = request.form.get("old_name", "")
    new_name = request.form.get("new_name", "")

    try:
        service.rename(old_name, new_name)
        flash("File renamed successfully.", "success")
    except ValueError as error:
        flash(str(error), "error")

    return redirect(url_for("index"))


@app.route("/delete", methods=["POST"])
def delete():
    name = request.form.get("name", "")

    try:
        service.delete(name)
        flash("File deleted successfully.", "success")
    except ValueError as error:
        flash(str(error), "error")

    return redirect(url_for("index"))


@app.route("/clear", methods=["POST"])
def clear():
    try:
        deleted_count = service.clear()
        flash(
            f"Workspace cleared. {deleted_count} file(s) removed.",
            "success",
        )
    except OSError:
        flash("Could not clear the workspace. Please try again.", "error")

    return redirect(url_for("index"))


@app.route("/api/stats")
def api_stats():
    return jsonify(service.stats())


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "app": "Sandhu Drive",
    }), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
