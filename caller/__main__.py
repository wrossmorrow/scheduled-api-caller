import argparse
from base64 import urlsafe_b64encode
from json import loads
from os.path import expandvars
import re
from typing import Tuple, Union

from .caller import Caller, FailedAPICall, HTTPMethod
from .logging import getLogger

logger = getLogger(__name__)


# status code conditions; eg. 4xx, 50X, 404, 000 (no connection)
HTTP_CODE_PATTERN = re.compile(r"^(000|[45][0-9]{2}|[45][0-9][xX]|[45][xX]{2})$")


def regex_failed_http_code(value: Union[int, str]) -> str:
    _value = value if isinstance(value, str) else f"{value:03d}"
    if HTTP_CODE_PATTERN.match(_value):
        return _value
    raise argparse.ArgumentTypeError(
        f'invalid HTTP code value "{value}"; should match \\{HTTP_CODE_PATTERN.pattern}\\'
    )


def http_auth_type(value: str) -> str:
    if re.match(r"[Bb](asic|earer)", value):
        return value.lower()
    raise argparse.ArgumentTypeError(
        f'invalid HTTP auth value "{value}"; should match \\([Bb]asic|[Bb]earer)\\'
    )


def kvp_type(value: str) -> Tuple[str, str]:
    if re.match(r"^[^= ]+=([^ ]+|\".*\")$", value):
        k, v = value.split("=", 1)
        if v.startswith('"') and v.endswith('"'):
            v = v[1:-1]
        return (k, v)
    raise argparse.ArgumentTypeError(
        f'invalid key-value pair "{value}"; should match \\^[^= ]+=([^ ]+|".*")$\\'
    )


def get_cli_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-u",
        "--host",
        type=str,
        help="Host to call (can use env vars)",
        required=True,
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        help="Port listening on host",
        default=None,
    )
    parser.add_argument(
        "-l",
        "--path",
        type=str,
        help="Resource path (can use env vars)",
        default="",
    )
    parser.add_argument(
        "-q",
        "--params",
        type=kvp_type,
        nargs="+",
        help="Query parameters as key-value pairs (e.g., 'status=201')",
        default=None,
    )
    parser.add_argument(
        "-m",
        "--method",
        type=str,
        choices=[m.value.lower() for m in HTTPMethod],
        help="HTTP method",
        default="get",
    )
    parser.add_argument(
        "-a",
        "--auth",
        type=http_auth_type,
        help="type of HTTP auth to use",
        default=None,
    )
    parser.add_argument(
        "-c",
        "--credentials",
        type=str,
        help="Credentials for HTTP auth (username:password or token, can use env vars)",
        default=None,
    )
    parser.add_argument(
        "-H",
        "--headers",
        type=kvp_type,
        nargs="+",
        help="additional HTTP headers as key-value pairs (eg, 'X-Request-Id=0', can use env vars)",
        default=None,
    )
    parser.add_argument(
        "-b",
        "--body",
        type=str,
        help="Request body as a json string (can use env vars)",
        default=None,
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=float,
        help="Timeout in seconds (per request)",
        default=60,
    )
    parser.add_argument(
        "-r",
        "--retries",
        type=int,
        help="Number of retries",
        default=0,
    )
    parser.add_argument(
        "-C",
        "--retry-on-codes",
        type=regex_failed_http_code,
        nargs="+",
        help=f"HTTP response codes to fail on (matching \\{HTTP_CODE_PATTERN.pattern}\\)",
        default=[0, "50X"],
    )
    parser.add_argument(
        "-f",
        "--fail-on-codes",
        type=regex_failed_http_code,
        nargs="+",
        help=f"HTTP response codes to fail on (matching \\{HTTP_CODE_PATTERN.pattern}\\)",
        default=[0, "50X"],
    )
    parser.add_argument(
        "-k",
        "--insecure",
        help="Don't use TLS (HTTPS)",
        default=False,
        action="store_true",
    )
    parser.add_argument(
        "--quiet",
        help="Don't log the response",
        default=False,
        action="store_true",
    )

    args = parser.parse_args()
    if args.port is None:
        args.port = 80 if args.insecure else 443
    if args.auth is not None:
        if args.headers is None:
            args.headers = []  # List of Tuples
        if args.credentials is None:
            raise ValueError("Must provide credentials (-c, --credentials) with auth")
        if args.auth == "basic":
            assert ":" in args.credentials, "Credentials must be in the form username:password"
            assert (
                len(args.credentials.split(":")) == 2
            ), "Credentials must be in the form username:password"
            # need to envsubst the credentials, because we base64 encode them
            args.credentials = urlsafe_b64encode(expandvars(args.credentials).encode()).decode()
            args.headers.append(("Authorization", f"Basic {args.credentials}"))
        elif args.auth == "bearer":
            args.headers.append(("Authorization", f"Bearer {args.credentials}"))

    # convert KVP's to dictionary
    if args.params:
        args.params = {key: value for key, value in args.params}
    if args.headers:
        args.headers = {key: value for key, value in args.headers}
    if args.body:
        args.body = loads(args.body)

    return args


if __name__ == "__main__":
    args = get_cli_args()

    try:
        results = Caller(
            host=args.host,
            port=args.port,
            insecure=args.insecure,
        )(
            method=HTTPMethod(args.method.upper()),
            path=args.path,
            params=args.params,
            headers=args.headers,
            body=args.body,
            timeout=args.timeout,
            retries=args.retries,
            retry_on=args.retry_on_codes,
            fail_on=args.fail_on_codes,
        )
    except FailedAPICall as err:
        logger.error(err)
        exit(1)

    if not args.quiet:
        logger.info(results)
