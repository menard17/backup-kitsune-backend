import math


def size_from_base64(image: str) -> int:
    prefix = "data:image/png;base64,"

    # Check format
    if (image_prefix := image[: len(prefix)]) != prefix:
        raise ValueError(f"Wrong format: {image_prefix}")
    base64_length = len(image) - len(prefix)

    # Check file size
    size_in_bytes = math.ceil(base64_length / 4) * 3
    return size_in_bytes - 2
