import requests
from flask import g, jsonify
from flask_httpauth import HTTPBasicAuth
from . import api
from .errors import unauthorized
from app.models import User

auth = HTTPBasicAuth()


@auth.verify_password
def verify_user(email_or_token, password):
    """The callback for HTTPBasicAuth

    Returns True for two types of user:
        1. AnonymousUser
        2. Normal User(via password or token)
        Returns False for invalid credentials.
    """
    if email_or_token == '':
        return True
    if password == '':
        g.user = User.verify_auth_token(email_or_token)
        g.token_used = True  # Set token to True in current request
        return g.user is not None
    user = User.query.filter_by(email=email_or_token).first()
    if user is None:
        return False
    g.user = user
    g.token_used = False
    return user.verify_password(password)


@auth.error_handler
def auth_error():
    """The callback function for login_required with incorrect credentials"""
    return unauthorized('Invalid credentials')


@api.before_request
@auth.login_required
def before_request():
    """ Verify user types via verify_user function"""
    pass


@api.route('/token')
def get_token():
    """Request to get a new token for user logged in via username/password"""
    # Using g.token_used to prevent user get a new token via old token
    # Before a request, the client will check whether a token is expired,
    # if expired:
    #       firstly, send a request to get contents via username/password
    #       secondly, send another request get new token via username/password
    if not g.user or g.token_used:
        return unauthorized('Invalid credentials')
    return jsonify({'user': g.user.to_json(), 'token': g.user.generate_auth_token(
        expiration=3600 * 24 * 365), 'expiration': 3600 * 24 * 365})
