from flask import Blueprint

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return '网站升级中'