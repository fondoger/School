from flask import jsonify, request
from . import api

'''
    This module defines some functions that generate
    responses with error messages.

    HTTP status code marks error type.
    For errors:
    {
        'code': 
        'message': 
    }
    
'''


def bad_request(message):
    """You requested a correct URL with incorrect format or incorrect data"""
    response = jsonify({'error': 'bad request', 'message': message})
    response.status_code = 400
    return response


def unauthorized(message):
    """We need to know who you are"""
    response = jsonify({'error': 'unauthorized', 'message': message})
    response.status_code = 401
    return response


def forbidden(message):
    """We know who you are and what you want, but you are not permitted"""
    response = jsonify({'error': 'forbidden', 'message': message})
    response.status_code = 403
    return response


def not_found(message):
    response = jsonify({'error': 'not found', 'message': message})
    response.status_code = 404
    return response


def internal_error(message):
    response = jsonify({'error': 'not found', 'message': message})
    response.status_code = 500
    return response


@api.errorhandler(400)
def error_handler_400(e):
    return bad_request(str(e))


@api.app_errorhandler(404)
@api.app_errorhandler(405)
def _handle_api_error(ex):
    if request.path.startswith('/api/v1'):
        # 404 errors are never handled on the blueprint level
        # unless raised from a view func so actual 404 errors,
        # i.e. "no route for it" defined, need to be handled
        # here on the application level
        return not_found('Url or Resource not found')
    else:
        return ex
