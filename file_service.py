
from pathlib import Path
from datetime import datetime
from werkzeug.utils import secure_filename


IMAGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".ico"
}

DOCUMENT_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".txt", ".rtf",
    ".xls", ".xlsx", ".csv", ".ppt", ".pptx",
    ".odt", ".ods"
}

AUDIO_EXTENSIONS = {
    ".mp3", ".wav", ".ogg", ".m4a", ".flac"
}

VIDEO_EXTENSIONS = {
    ".mp4", ".webm", ".mov", ".mkv"
}

BLOCKED_EXTENSIONS = {
    ".exe", ".bat", ".cmd", ".com", ".msi",
    ".sh", ".ps1", ".scr", ".dll", ".vbs"
}

MAX_FILE_SIZE = 500 * 1024 * 1024


class FileService:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _safe_existing(self, name):
        if not isinstance(name, str) or not name:
            return None

        if name in {".", ".."}:
            return None

        if "/" in name or "\\" in name or "\x00" in name:
            return None

        candidate = self.root / name

        try:
            if candidate.is_symlink():
                return None

            resolved = candidate.resolve()

            if resolved.parent != self.root:
                return None

            if not candidate.is_file():
                return None

            return candidate

        except (OSError, ValueError):
            return None

    def resolve_name(self, name):
        path = self._safe_existing(name)
        return path.name if path else None

    @staticmethod
    def format_size(size):
        if size < 1024:
            return f"{size} B"

        if size < 1024 ** 2:
            return f"{size / 1024:.1f} KB"

        if size < 1024 ** 3:
            return f"{size / (1024 ** 2):.2f} MB"

        return f"{size / (1024 ** 3):.2f} GB"

    @staticmethod
    def get_category(extension):
        if extension in IMAGE_EXTENSIONS:
            return "Image"

        if extension in DOCUMENT_EXTENSIONS:
            return "Document"

        if extension in AUDIO_EXTENSIONS:
            return "Audio"

        if extension in VIDEO_EXTENSIONS:
            return "Video"

        return "Other"

    def list_files(self):
        files = []

        for path in self.root.iterdir():
            if (
                path.is_symlink()
                or not path.is_file()
                or path.name.startswith(".")
            ):
                continue

            try:
                file_stat = path.stat()
            except OSError:
                continue

            extension = path.suffix.lower()

            files.append({
                "name": path.name,
                "size": file_stat.st_size,
                "size_label": self.format_size(file_stat.st_size),
                "modified": datetime.fromtimestamp(
                    file_stat.st_mtime
                ).strftime("%d %b %Y · %I:%M %p"),
                "category": self.get_category(extension),
                "extension": extension[1:].upper() if extension else "FILE",
            })

        return sorted(
            files,
            key=lambda item: item["name"].casefold()
        )

    def stats(self):
        files = self.list_files()
        total_bytes = sum(item["size"] for item in files)

        return {
            "count": len(files),
            "bytes": total_bytes,
            "size_mb": round(total_bytes / (1024 * 1024), 2),
            "size_label": self.format_size(total_bytes),
            "images": sum(
                item["category"] == "Image" for item in files
            ),
            "documents": sum(
                item["category"] == "Document" for item in files
            ),
            "audio": sum(
                item["category"] == "Audio" for item in files
            ),
            "video": sum(
                item["category"] == "Video" for item in files
            ),
            "other": sum(
                item["category"] == "Other" for item in files
            ),
        }

    def _unique_name(self, name):
        candidate = name
        stem = Path(name).stem
        extension = Path(name).suffix
        counter = 1

        while (self.root / candidate).exists():
            candidate = f"{stem} ({counter}){extension}"
            counter += 1

        return candidate

    def save_upload(self, uploaded):
        original_name = secure_filename(uploaded.filename or "")

        if not original_name:
            raise ValueError("Please provide a valid filename.")

        extension = Path(original_name).suffix.lower()

        if extension in BLOCKED_EXTENSIONS:
            raise ValueError("Executable files are not allowed.")

        stream = uploaded.stream

        try:
            stream.seek(0, 2)
            file_size = stream.tell()
            stream.seek(0)
        except (OSError, AttributeError):
            raise ValueError("Could not read the uploaded file.")

        if file_size > MAX_FILE_SIZE:
            raise ValueError("File exceeds the 500 MB upload limit.")

        final_name = self._unique_name(original_name)
        destination = self.root / final_name

        uploaded.save(destination)
        return final_name

    def rename(self, old_name, new_name):
        old_path = self._safe_existing(old_name)

        if not old_path:
            raise ValueError("The original file was not found.")

        cleaned_name = secure_filename((new_name or "").strip())

        if not cleaned_name:
            raise ValueError("Please enter a valid filename.")

        if cleaned_name in {".", ".."}:
            raise ValueError("Invalid filename.")

        if cleaned_name == old_path.name:
            return

        destination = self.root / cleaned_name

        if destination.exists() or destination.is_symlink():
            raise ValueError("A file with this name already exists.")

        old_path.rename(destination)

    def delete(self, name):
        path = self._safe_existing(name)

        if not path:
            raise ValueError("The file could not be found.")

        path.unlink()

    def clear(self):
        deleted_count = 0

        for path in self.root.iterdir():
            if path.is_symlink():
                continue

            if path.is_file() and not path.name.startswith("."):
                path.unlink()
                deleted_count += 1

        return deleted_count
