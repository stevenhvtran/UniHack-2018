from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Gig(db.Model):
    __tablename__ = 'gig'
    id = db.Column(db.Integer, primary_key=True)
    gig_name = db.Column(db.Text, nullable=False)
    playlist_id = db.Column(db.Text)
    playlist_url = db.Column(db.Text)
    playlist_uri = db.Column(db.Text)
    settings = db.Column(db.Text)
    users = db.relationship('User', backref='gig')


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    access_token = db.Column(db.Text, unique=True, nullable=False)
    is_host = db.Column(db.Boolean, default=False)
    spotify_id = db.Column(db.Text, nullable=True)
    top_tracks = db.Column(db.Text, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    gig_id = db.Column(db.Integer, db.ForeignKey('gig.id'))
