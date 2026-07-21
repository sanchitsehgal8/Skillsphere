import pytest

from app.services.codeforces_analyzer import normalize_handle


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("tourist", "tourist"),
        ("@tourist", "tourist"),
        ("https://codeforces.com/profile/tourist", "tourist"),
        ("codeforces.com/profile/Petr/", "Petr"),
        ("", ""),
        ("   ", ""),
    ],
)
def test_normalize_handle(raw, expected):
    assert normalize_handle(raw) == expected
