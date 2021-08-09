"""Test the decode router with authenticated user."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from fastapi.testclient import TestClient
    from pytest_mock import MockFixture

    from image_secrets.backend.database.image.models import DecodedImage
    from image_secrets.backend.database.user.models import User

URL = "/decode"


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
    insert_decoded: DecodedImage,
) -> None:
    """Test the get request."""
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
    image = json_[0]
    assert image["image_name"] == insert_decoded.image_name
    assert image["message"] == insert_decoded.message
    assert image["delimiter"] == insert_decoded.delimiter
    assert image["lsb_amount"] == insert_decoded.lsb_amount


@pytest.mark.parametrize(
    "delimiter, lsb_n",
    [
        ("dlm1", 1),
        ("dlm2", 2),
        ("dlm3", 3),
        ("dlm5", 4),
        ("dlm5", 5),
        ("dlm6", 6),
        ("dlm7", 7),
        ("dlm8", 8),
    ],
)
def test_post(
    api_client: TestClient,
    auth_token: tuple[dict[str, str], User],
    api_image_file,
    test_image_path: Path,
    mocker: MockFixture,
    delimiter: str,
    lsb_n: int,
) -> None:
    """Test a successful post request."""
    buffer = api_image_file["file"][1]

    decode_api = mocker.patch(
        "image_secrets.backend.decode.api",
        return_value=("decoded>test", test_image_path),
    )

    header = auth_token[0]
    response = api_client.post(
        URL,
        files=api_image_file,
        data={
            "custom-delimiter": delimiter,
            "least-significant-bit-amount": lsb_n,
        },
        headers=header,
    )

    decode_api.assert_called_once_with(
        image_data=buffer,
        delimiter=delimiter,
        lsb_n=lsb_n,
        reverse=False,
    )

    response.raise_for_status()
    assert response.status_code == 201
    assert response.reason == "Created"
    json_ = response.json()
    assert json_["image_name"] == "test.png"
    assert json_["message"] == "decoded>test"
    assert json_["delimiter"] == delimiter
    assert json_["lsb_amount"] == lsb_n


def test_post_200(
    api_client: TestClient,
    auth_token: tuple[dict[str, str], User],
    mocker: MockFixture,
    test_image_path: Path,
    api_image_file,
) -> None:
    """Test a post request with valid request but no decoded result."""
    buffer = api_image_file["file"][1]

    decode_api = mocker.patch(
        "image_secrets.backend.decode.api",
    )
    decode_api.side_effect = StopIteration("test exception")

    header = auth_token[0]
    response = api_client.post(
        URL,
        files=api_image_file,
        data={
            "custom-delimiter": "delimiter",
            "least-significant-bit-amount": 1,
        },
        headers=header,
    )

    decode_api.assert_called_once_with(
        image_data=buffer,
        delimiter="delimiter",
        lsb_n=1,
        reverse=False,
    )

    response.raise_for_status()
    assert response.status_code == 200
    assert response.reason == "OK"
    assert response.json()["detail"] == "test exception"
    headers = response.headers
    assert headers["custom-delimiter"] == "delimiter"
    assert headers["least-significant-bit-amount"] == repr(1)


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
        headers=header,
    )

    assert response.status_code == 415
    assert response.reason == "Unsupported Media Type"
    assert response.json()["detail"] == "only .png images are supported"


def test_get_images(
    api_client: TestClient,
    auth_token: tuple[dict[str, str], User],
    insert_decoded: DecodedImage,
) -> None:
    """Test a successful get request for decoded images with specified name."""
    header = auth_token[0]
    response = api_client.get(
        f"{URL}/{insert_decoded.image_name}",
        headers=header,
    )

    assert response.status_code == 200
    assert response.reason == "OK"
    json_ = response.json()
    assert isinstance(json_, list)
    image = json_[0]
    assert image["image_name"] == insert_decoded.image_name
    assert image["message"] == insert_decoded.message
    assert image["delimiter"] == insert_decoded.delimiter
    assert image["lsb_amount"] == insert_decoded.lsb_amount


@pytest.mark.parametrize("image_name", ["test_name", "test_url", "10"])
def test_get_images_404(
    api_client: TestClient,
    auth_token: tuple[dict[str, str], User],
    image_name: str,
) -> None:
    """Test a successful get request for decoded images without finding any results."""
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
        == f"no decoded image(s) with name {image_name!r} found"
    )
