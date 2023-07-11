from flask_cors import CORS


def init_app(app):
    """Initializes extension"""
    CORS(app)
