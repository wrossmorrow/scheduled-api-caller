from __future__ import annotations

import logging
from time import sleep
from typing import Dict, Tuple
from uuid import uuid4

from flask import Flask, jsonify, request, Response
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth

DEFAULT_CODES = {
    "GET": 200,
    "PUT": 201,
    "POST": 201,
    "PATCH": 200,
    "DELETE": 204,
}

ALL_METHODS = list(DEFAULT_CODES.keys())

REQUEST_COUNT: Dict[str, int] = {}


def setup_logger(app: Flask, level: int = logging.INFO) -> None:
    formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
    app.logger.handlers[0].setFormatter(formatter)
    app.logger.setLevel(level)


app = Flask(__name__)
basic_auth = HTTPBasicAuth()
bearer_auth = HTTPTokenAuth()
setup_logger(app)


@app.before_request
def log_request() -> None:
    if request.get_json(silent=True):
        app.logger.info(
            " ".join(
                [
                    request.method,
                    request.path,
                    str(request.get_json()),
                ]
            )
        )


@basic_auth.verify_password
def verify_password(username: str, password: str) -> bool:
    if username and password:
        return True
    return False


@bearer_auth.verify_token
def verify_token(token: str) -> bool:
    if token:
        return True
    return False


def get_int_from_params(key: str, default: int = 0) -> int:
    try:
        return int(request.args.get(key, default))
    except ValueError as err:
        app.logger.error(
            f"Error getting int {key} from params ({request.args.get(key)}): {err.__class__.__name__}: {err}"
        )
        return 0


def respond(subpath: str) -> Tuple[Response, int]:
    # get or assign request_id
    request_id = request.headers.get("X-Request-Id", request.args.get("requestId", str(uuid4())))
    if request_id in REQUEST_COUNT:
        REQUEST_COUNT[request_id] += 1
    else:
        REQUEST_COUNT[request_id] = 1

    # maybe wait to respond, depending on query params
    wait = get_int_from_params("wait")
    if wait > 0:
        sleep(wait)

    # get desired status code from query params, or default for method
    status = get_int_from_params("status", default=DEFAULT_CODES[request.method])
    fails = get_int_from_params("fails")
    if fails > 0 and REQUEST_COUNT[request_id] <= fails:
        status = 500

    response = jsonify({"subpath": ("/" if subpath else "") + subpath})
    response.headers["X-Request-Id"] = request_id

    return response, status


# Routes
#
#   GET /status/health always responds 200
#   GET /admin/count/{id} gets a count (or 0) for the request id
#   POST /admin/clear/{id} resets the count (to 0) for the request id
#   POST /admin/reset clears all counts (to 0)
#   ALL /noauth(/*) does not require auth
#   ALL /basic(/*) requires basic auth (any username/password)
#   ALL /bearer(/*) requires bearer auth (any token)
#
#   each of the last three reply with the supplied subpath in JSON
#   accepted query params (for any method) are:
#   * status: int (the desired status code of the response)
#   * wait: int (sleep for this many seconds before responding)
#   * fails: int (number of times to fail with 500 before succeeding)
#   failing works by tracking X-Request-Id in the request/response headers
#   if one is supplied in the request headers or params, it is used in the response.
#


@app.route("/status/health")
def health_check() -> Tuple[Response, int]:
    return jsonify({"status": "UP"}), 200


@app.route("/admin/count/<string:request_id>", methods=["GET"])
def request_count(request_id: str) -> Tuple[Response, int]:
    global REQUEST_COUNT
    return jsonify({"count": REQUEST_COUNT.get(request_id, 0)}), 200


@app.route("/admin/clear/<string:request_id>", methods=["POST"])
def request_clear(request_id: str) -> Tuple[Response, int]:
    global REQUEST_COUNT
    if request_id in REQUEST_COUNT:
        del REQUEST_COUNT[request_id]
    return jsonify({"count": REQUEST_COUNT.get(request_id, 0)}), 200


@app.route("/admin/reset", methods=["POST"])
def request_reset() -> Tuple[Response, int]:
    global REQUEST_COUNT
    REQUEST_COUNT = {}
    return jsonify({}), 200


@app.route("/noauth", methods=ALL_METHODS)
def noauth_request() -> Tuple[Response, int]:
    return respond("")


@app.route("/noauth/<path:subpath>", methods=ALL_METHODS)
def noauth_request_path(subpath: str) -> Tuple[Response, int]:
    return respond(subpath)


@app.route("/basic", methods=ALL_METHODS)
@basic_auth.login_required
def basic_request() -> Tuple[Response, int]:
    return respond("")


@app.route("/basic/<path:subpath>", methods=ALL_METHODS)
@basic_auth.login_required
def basic_request_path(subpath: str) -> Tuple[Response, int]:
    return respond(subpath)


@app.route("/bearer", methods=ALL_METHODS)
@bearer_auth.login_required
def bearer_request() -> Tuple[Response, int]:
    return respond("")


@app.route("/bearer/<path:subpath>", methods=ALL_METHODS)
@bearer_auth.login_required
def bearer_request_path(subpath: str) -> Tuple[Response, int]:
    return respond(subpath)
