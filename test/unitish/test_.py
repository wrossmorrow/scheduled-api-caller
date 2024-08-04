from base64 import urlsafe_b64encode
from dataclasses import dataclass
from os.path import expandvars
import re  # noqa: F401
from typing import Dict, List, Optional, Union

from caller.caller import Caller, HTTPMethod
import pytest

TEST_HOST = "localhost"
TEST_PORT = 8080

BASIC_AUTH_CREDENTIALS = urlsafe_b64encode("username:password".encode()).decode()
BASIC_AUTH_HEADERS = {"Authorization": f"Basic {BASIC_AUTH_CREDENTIALS}"}
BEARER_AUTH_HEADERS = {"Authorization": "Bearer token"}


@dataclass
class InternalTestRequest:
    host: str = TEST_HOST
    port: int = TEST_PORT
    path: Optional[str] = None
    params: Optional[Dict] = None
    method: HTTPMethod = HTTPMethod.GET
    headers: Optional[Dict] = None
    body: Optional[Dict] = None
    timeout: float = 60.0
    retries: int = 0
    retry_on: Optional[
        List[Union[int, str]]
    ] = None  # re.Pattern = re.compile(r"(000|5[0-9][0-9])")


@dataclass
class InternalTestResponse:
    status: int = 200


@dataclass
class InternalTestCase:
    request: InternalTestRequest
    response: InternalTestResponse


@pytest.mark.parametrize(
    "InternalTestCase",
    (
        InternalTestCase(
            request=InternalTestRequest(
                path="/noauth",
            ),
            response=InternalTestResponse(),
        ),
        InternalTestCase(
            request=InternalTestRequest(
                path="/basic",
                headers=BASIC_AUTH_HEADERS,
            ),
            response=InternalTestResponse(),
        ),
        InternalTestCase(
            request=InternalTestRequest(
                path="/bearer",
                headers=BEARER_AUTH_HEADERS,
            ),
            response=InternalTestResponse(),
        ),
        InternalTestCase(
            request=InternalTestRequest(
                path="/bearer",
                headers=BASIC_AUTH_HEADERS,
            ),
            response=InternalTestResponse(status=401),
        ),
        InternalTestCase(
            request=InternalTestRequest(
                path="/noauth/subpath",
                params={"status": 301},
            ),
            response=InternalTestResponse(status=301),
        ),
        InternalTestCase(
            request=InternalTestRequest(
                path="/noauth${HOME}",
                params={"status": 301},
            ),
            response=InternalTestResponse(status=301),
        ),
        InternalTestCase(
            request=InternalTestRequest(
                method=HTTPMethod.POST,
                path="/noauth",
            ),
            response=InternalTestResponse(status=201),
        ),
        InternalTestCase(
            request=InternalTestRequest(
                method=HTTPMethod.DELETE,
                path="/noauth",
            ),
            response=InternalTestResponse(status=204),
        ),
    ),
)
def test_(InternalTestCase: InternalTestCase) -> None:
    results = Caller(
        host=InternalTestCase.request.host,
        port=InternalTestCase.request.port,
        insecure=True,
    )(
        method=InternalTestCase.request.method,
        path=InternalTestCase.request.path,
        params=InternalTestCase.request.params,
        headers=InternalTestCase.request.headers,
        body=InternalTestCase.request.body,
        timeout=InternalTestCase.request.timeout,
        retries=InternalTestCase.request.retries,
        retry_on=InternalTestCase.request.retry_on,
    )
    print(results)

    assert results[-1].status == InternalTestCase.response.status

    if isinstance(results[-1].body, dict) and results[-1].body["subpath"]:
        realpath = expandvars(InternalTestCase.request.path or "")
        if realpath:
            subpath = "/" + "/".join(realpath.split("/")[(2 if realpath[0] == "/" else 1) :])
            assert subpath == results[-1].body["subpath"]
