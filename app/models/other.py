from flask import g
from datetime import datetime
from .. import db

class TempImage(db.Model):
    __tablename__ = 'temp_images'
    url = db.Column(db.String(64), primary_key=True)
    time = db.Column(db.Integer)
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    type = db.Column(db.String(16))
    theme_color = db.Column(db.String(8))