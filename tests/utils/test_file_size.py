import pytest

from utils.file_size import size_from_base64


@pytest.fixture
def base64_image():
    with open("./artifact/image_base64") as f:
        photo_base64 = f.readlines()[0]
    yield photo_base64


def test_correct_format_size(base64_image):
    pixel_size = 104
    assert size_from_base64(base64_image) <= (pixel_size**2) * 3


def test_wrong_format(base64_image):
    cp_base64_image = base64_image[10:]
    with pytest.raises(ValueError, match=r"Wrong format: .*"):
        size_from_base64(cp_base64_image)
