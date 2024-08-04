from os import environ

from . import app

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8080

if __name__ == "__main__":
    host = environ.get("HOST", DEFAULT_HOST)
    port = int(environ.get("PORT", DEFAULT_PORT))
    app.run(host=host, port=port)
