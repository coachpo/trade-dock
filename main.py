from flask import Flask
from app.routes import init_app

app = Flask(__name__, template_folder="app/templates/", static_folder="app/static/")
init_app(app)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8088, debug=None)
