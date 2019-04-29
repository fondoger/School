from flask import request
from app import socketio
from flask_socketio import emit

clients = []


@socketio.on('connect')
def connected():
    clients.append(request.namespace)
    print("connected" + request.namespace)


@socketio.on('message')
def un_named_message(message, dd):
    print('un_named_message:', message, dd)
    emit("message2", "你好呀")


@socketio.on('disconnect')
def disconnect():
    clients.remove(request.namespace)
    print("disconnected" + request.namespace)
    return "222"
