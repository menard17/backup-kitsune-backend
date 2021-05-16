from get_zoom_jwt import get_zoom_jwt
from flask import Flask

app = Flask(__name__)

app.add_url_rule("/zoom_jwt", view_func=get_zoom_jwt, methods=["GET"])

if __name__ == "__main__":
    # Used when running locally only. When deploying to Cloud Run,
    # a webserver process such as Gunicorn will serve the app.
    app.run(host="localhost", port=8080, debug=True)
