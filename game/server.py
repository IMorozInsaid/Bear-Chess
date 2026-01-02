
from flask import Flask
from flask_socketio import SocketIO, emit, join_room, leave_room
import random

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

rooms = {}

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('create_room')
def create_room():
    room = str(random.randint(1000, 9999))
    rooms[room] = {'players': 1, 'board': Board.copy(), 'turn': 0}  # Copy initial board
    join_room(room)
    emit('room_created', {'room': room})

@socketio.on('join_room')
def join_room(data):
    room = data['room']
    if room in rooms and rooms[room]['players'] == 1:
        rooms[room]['players'] = 2
        join_room(room)
        emit('joined', {'success': True})
        emit('start_game', rooms[room], room=room)
    else:
        emit('joined', {'success': False})

@socketio.on('move')
def handle_move(data):
    room = data['room']
    if room in rooms:
        # Update board with move
        from_pos = data['from']
        to_pos = data['to']
        # Perform move on server board
        perform_move(from_pos, to_pos, rooms[room]['board'])  # Adapt perform_move to take board as param
        emit('move', data, room=room)

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)