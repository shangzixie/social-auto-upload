from pathlib import Path


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
    ".webm",
    ".flv",
    ".wmv",
    ".m4v",
}


def normalize_content_type(content_type):
    if not content_type:
        return "video"
    normalized = str(content_type).strip().lower()
    if normalized in {"video", "image"}:
        return normalized
    return "video"


def is_image_file(file_name):
    return Path(str(file_name)).suffix.lower() in IMAGE_EXTENSIONS


def is_video_file(file_name):
    return Path(str(file_name)).suffix.lower() in VIDEO_EXTENSIONS


def validate_xiaohongshu_publish_payload(content_type, file_list):
    normalized_type = normalize_content_type(content_type)
    if normalized_type != "image":
        return

    if not file_list:
        raise ValueError("小红书图文发布至少需要 1 张图片")

    if len(file_list) > 9:
        raise ValueError("小红书图文单次最多支持 9 张图片")

    invalid_files = [file_name for file_name in file_list if not is_image_file(file_name)]
    if invalid_files:
        raise ValueError("小红书图文仅支持图片文件（jpg/jpeg/png/webp）")
