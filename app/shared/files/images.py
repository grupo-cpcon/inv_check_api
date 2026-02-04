import magic

def detect_image_extension(data: bytes) -> str:
    mime = magic.from_buffer(data, mime=True)

    if not mime or not mime.startswith("image/"):
        return "bin"

    return mime.split("/")[-1]
