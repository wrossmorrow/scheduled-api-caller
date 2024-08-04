from base64 import b64encode

from caller.__main__ import kvp_type
import pytest


def strb64(s: str) -> str:
    return b64encode(s.encode()).decode()


@pytest.mark.parametrize(
    "arg, name, value",
    [
        ("key=value", "key", "value"),
        ('key="value"', "key", "value"),
        (
            'key="value with spaces argparse wouldn\'t understand"',
            "key",
            "value with spaces argparse wouldn't understand",
        ),
        (
            f'key={strb64("this string has == in it.")}',
            "key",
            strb64("this string has == in it."),
        ),
        (
            f'key="{strb64("this string has == in it.")}"',
            "key",
            strb64("this string has == in it."),
        ),
    ],
)
def test_arg_parse_kvp_type(arg: str, name: str, value: str) -> None:
    key, value = kvp_type(arg)
    assert key == name
    assert value == value
