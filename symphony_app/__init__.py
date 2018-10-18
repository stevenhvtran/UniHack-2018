import os
from flask import Flask
from flask_cors import CORS


def create_app():
    """
    Creates the Flask app using an application factory setup
    :return: The app as a Flask object
    """
    app = Flask(__name__)
    app.config.from_mapping({
        'SECRET_KEY': os.environ['SECRET_KEY'],
        'SQLALCHEMY_DATABASE_URI': os.environ['DATABASE_URL'],
        'SQLALCHEMY_TRACK_MODIFICATIONS': False
    })
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    from symphony_app.db import db
    db.init_app(app)

    with app.test_request_context():

        db.create_all()

        from symphony_app import symphony
        app.register_blueprint(symphony.bp)

        return app
