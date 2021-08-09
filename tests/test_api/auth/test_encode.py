"""Test the encode router with authenticated user."""
from __future__ import annotations

import asyncio
from json import JSONDecodeError
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from fastapi.testclient import TestClient
    from pytest_mock import MockFixture

    from image_secrets.backend.database.image.models import EncodedImage
    from image_secrets.backend.database.user.models import User


URL = "/encode"


def test_get_empty(
    api_client: TestClient,
    auth_token: tuple[dict[str, str], User],
) -> None:
    """Test the get request with no stored images."""
    header = auth_token[0]
    response = api_client.get(
        URL,
        headers=header,
    )

    response.raise_for_status()
    assert response.status_code == 200
    assert response.reason == "OK"
    json_ = response.json()
    assert isinstance(json_, list)
    assert not json_
    assert response.headers["content-length"] == "2"


def test_get(
    api_client: TestClient,
    auth_token: tuple[dict[str, str], User],
) -> None:
    """Test successful get request."""
    header = auth_token[0]
    user = auth_token[1]

    from image_secrets.backend.database.image.models import EncodedImage

    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        EncodedImage.create(
            filename="filename",
            image_name="image_name",
            message="message",
            delimiter="delimiter",
            owner_id=user.id,
        ),
    )

    response = api_client.get(
        URL,
        headers=header,
    )

    response.raise_for_status()
    assert response.status_code == 200
    assert response.reason == "OK"
    json_ = response.json()
    assert isinstance(json_, list)
    image = json_[0]
    assert image["image_name"] == "image_name"
    assert image["message"] == "message"
    assert image["delimiter"] == "delimiter"
    assert image["lsb_amount"] == 1


@pytest.mark.parametrize(
    "message, delimiter, lsb_n",
    [
        ("test1", "dlm1", 1),
        ("test2", "dlm2", 2),
        ("test3", "dlm3", 3),
        ("test4", "dlm5", 4),
        ("test5", "dlm5", 5),
        ("test6", "dlm6", 6),
        ("test7", "dlm7", 7),
        ("test8", "dlm8", 8),
    ],
)
def test_post(
    api_client: TestClient,
    auth_token: tuple[dict[str, str], User],
    api_image_file,
    test_image_path: Path,
    mocker: MockFixture,
    message: str,
    delimiter: str,
    lsb_n: int,
) -> None:
    """Test a successful post request."""
    buffer = api_image_file["file"][1]

    encode_api = mocker.patch(
        "image_secrets.backend.encode.api",
        return_value=test_image_path,
    )

    header = auth_token[0]
    response = api_client.post(
        URL,
        files=api_image_file,
        data={
            "message": message,
            "custom-delimiter": delimiter,
            "least-significant-bit-amount": lsb_n,
        },
        headers=header,
    )

    encode_api.assert_called_once_with(
        message=message,
        file=buffer,
        delimiter=delimiter,
        lsb_n=lsb_n,
        reverse=False,
    )

    response.raise_for_status()
    assert response.status_code == 201
    assert response.reason == "Created"
    with pytest.raises(JSONDecodeError):  # png image data should be returned
        response.json()
    headers = response.headers
    assert headers["image-name"] == "test.png"
    assert headers["message"] == message
    assert headers["delimiter"] == delimiter
    assert headers["lsb_amount"] == repr(lsb_n)
    assert headers["content-type"] == "image/png"
    assert 'filename="test.png"' in headers["content-disposition"]


def test_post_image_too_small(
    api_client: TestClient,
    api_image_file,
    auth_token: tuple[dict[str, str], User],
) -> None:
    """Test a post request with a message longer than fits into the uploaded image."""
    header = auth_token[0]
    msg = "test" * 1000
    response = api_client.post(
        URL,
        files=api_image_file,
        data={"message": msg},
        headers=header,
    )

    assert response.status_code == 422
    assert response.reason == "Unprocessable Entity"
    json_ = response.json()
    assert json_["field"] == "file"
    headers = response.headers
    assert headers["image-name"] == "test.png"
    assert headers["message"] == msg
    assert headers["delimiter"] == "<{~stop-here~}>"
    assert headers["lsb_amount"] == repr(1)


def test_post_415(
    api_client: TestClient,
    auth_token: tuple[dict[str, str], User],
) -> None:
    """Test a post request with invalid media type."""
    header = auth_token[0]
    response = api_client.post(
        URL,
        files={
            "file": (Path(__file__).name, open(__file__).read(), "image/png"),
        },
        data={"message": "test"},
        headers=header,
    )

    assert response.status_code == 415
    assert response.reason == "Unsupported Media Type"
    assert response.json()["detail"] == "only .png images are supported"


def test_get_images(
    api_client: TestClient,
    auth_token: tuple[dict[str, str], User],
    insert_encoded: EncodedImage,
) -> None:
    """Test a successful get request for encoded images with specified name."""
    header = auth_token[0]
    response = api_client.get(
        f"{URL}/{insert_encoded.image_name}",
        headers=header,
    )

    assert response.status_code == 200
    assert response.reason == "OK"
    json_ = response.json()
    assert isinstance(json_, list)
    image = json_[0]
    assert image["image_name"] == insert_encoded.image_name
    assert image["message"] == insert_encoded.message
    assert image["delimiter"] == insert_encoded.delimiter
    assert image["lsb_amount"] == insert_encoded.lsb_amount


@pytest.mark.parametrize("image_name", ["test_name", "test_url", "10"])
def test_get_images_404(
    api_client: TestClient,
    auth_token: tuple[dict[str, str], User],
    image_name: str,
) -> None:
    """Test a successful get request for encoded images without finding any results."""
    header = auth_token[0]
    response = api_client.get(
        f"{URL}/{image_name}",
        headers=header,
    )

    assert response.status_code == 404
    assert response.reason == "Not Found"
    json_ = response.json()
    assert (
        json_["detail"]
        == f"no encoded image(s) with name {image_name!r} found"
    )
