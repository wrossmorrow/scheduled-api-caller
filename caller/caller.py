from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from json import dumps, JSONDecodeError, loads
from os import environ
from os.path import expandvars
from random import random
import re
from time import sleep
from typing import Dict, List, Optional, Union

import requests

from .logging import getLogger, new_log_context_vars

logger = getLogger(__name__)

DEFAULT_HEADERS = loads(environ.get("DEFAULT_HEADERS", "{}"))


class HTTPMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


@dataclass
class HTTPResponse:
    duration: float
    status: int
    headers: Dict
    body: Union[str, Dict]

    def __repr__(self) -> str:
        return dumps(asdict(self))

    @staticmethod
    def from_error(err: requests.RequestException) -> HTTPResponse:
        if not err.response:
            return HTTPResponse(
                duration=0,
                status=0,
                headers={},
                body={
                    "error": err.__class__.__name__,
                    "message": str(err),
                },
            )

        return HTTPResponse(
            duration=err.response.elapsed.total_seconds(),
            status=err.response.status_code,
            headers={},
            body={
                "error": err.__class__.__name__,
                "message": str(err),
            },
        )

    @staticmethod
    def from_requests_response(response: requests.Response) -> HTTPResponse:
        try:
            return HTTPResponse(
                duration=response.elapsed.total_seconds(),
                status=response.status_code,
                headers=dict(response.headers),
                body=loads(response.text),
            )
        except JSONDecodeError:
            return HTTPResponse(
                duration=response.elapsed.total_seconds(),
                status=response.status_code,
                headers=dict(response.headers),
                body=response.text,
            )


def expandvars_dict(data: Optional[Dict]) -> Optional[Dict]:
    if not data:
        return data
    return {
        key: (expandvars(value) if isinstance(value, str) else value) for key, value in data.items()
    }


def patternize_codes(
    codes: Optional[List[Union[int, str]]],
) -> re.Pattern:
    if not codes:
        return re.compile(r"(000)")
    _codes = [
        code if isinstance(code, str) else f"{code:03d}"
        for code in codes
        if isinstance(code, str) or (100 <= code < 600 or code == 0)
    ]
    return re.compile("(" + "|".join(_codes).replace("X", "[0-9]").replace("x", "[0-9]") + ")")


class FailedAPICall(Exception):
    status: int
    attempts: int
    responses: List[HTTPResponse]

    def __init__(self, message: str, responses: List[HTTPResponse]) -> None:
        super().__init__(message)
        self.status = responses[-1].status if responses else 0
        self.attempts = len(responses)
        self.responses = responses


@dataclass
class Caller:
    host: str
    port: int
    insecure: bool = False

    def __call__(
        self,
        method: HTTPMethod = HTTPMethod.GET,
        path: Optional[str] = None,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        body: Optional[Dict] = None,
        timeout: float = 60.0,
        retries: int = 0,
        retry_on: Optional[List[Union[int, str]]] = None,
        fail_on: Optional[List[Union[int, str]]] = None,
    ) -> List[HTTPResponse]:
        if not path:
            path = ""
        elif path[0] == "/":
            path = path[1:]

        # # TODO: choose if this is set; may affect testing convenience at least
        # if params and method != HTTPMethod.GET:
        #     raise ValueError(f"{method.value} requests cannot have query parameters")

        if method in [HTTPMethod.GET, HTTPMethod.DELETE] and body is not None:
            raise ValueError(f"{method.value} requests cannot have a body")
        elif body is None:
            body = {}

        sch = "http" if self.insecure else "https"
        mtd = method.value.lower()
        url = f"{sch}://{expandvars(self.host)}:{self.port}/{expandvars(path)}"
        prm = expandvars_dict(params)
        hdr = expandvars_dict({**DEFAULT_HEADERS, **headers} if headers else DEFAULT_HEADERS)
        bdy = expandvars_dict(body)

        # add call context to logs, excluding rendering from environment variables
        # which may contain secrets
        new_log_context_vars(
            scheme=sch,
            method=mtd,
            host=self.host,
            path=path,
            headers=headers,
            params=params,
        )

        logger.info("Making request")

        _retry_on = patternize_codes(retry_on)
        _fail_on = patternize_codes(fail_on)

        responses: List[HTTPResponse] = []

        attempt = 0
        while attempt <= retries:
            response: HTTPResponse
            try:
                if method == HTTPMethod.GET or method == HTTPMethod.DELETE:
                    response = HTTPResponse.from_requests_response(
                        requests.request(
                            method=mtd, url=url, params=prm, headers=hdr, timeout=timeout
                        )
                    )
                else:
                    response = HTTPResponse.from_requests_response(
                        requests.request(
                            method=mtd, url=url, params=prm, headers=hdr, json=bdy, timeout=timeout
                        )
                    )
            except requests.exceptions.RequestException as err:
                response = HTTPResponse.from_error(err)

            responses.append(response)

            if _retry_on.match(f"{response.status:03d}") and attempt < retries:
                backoff = 2**attempt + random() / 2.0
                logger.warning(
                    f"response ({response.status}) matches retry_on ({_retry_on.pattern})"
                    f"; retrying in {backoff:.2f} seconds"
                )
                attempt += 1
                sleep(backoff)
            else:
                break

        last_status = f"{responses[-1].status:03d}"
        if _fail_on.match(last_status):
            logger.error("Failing due to status code", status_code=last_status)
            raise FailedAPICall(f"Failing due to status code {last_status}", responses)

        logger.info("Succeeded on status code", status_code=last_status)
        return responses
