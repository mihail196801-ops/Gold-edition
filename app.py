from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my_secret_key'
# cors_allowed_origins="*" разрешает подключение с любых доменов (или IP)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Хранилище активных пользователей в комнатах
rooms = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def on_connect():
    print(f'Клиент подключился: {request.sid}')

@socketio.on('disconnect')
def on_disconnect():
    # Уведомляем комнату, что пользователь ушел
    room = request.args.get('room') if 'room' in request.args else None
    if room:
        emit('status', {'msg': 'Пользователь отключился', 'type': 'system'}, room=room)

@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    
    join_room(room)
    
    # Добавляем в список пользователей комнаты
    if room not in rooms:
        rooms[room] = []
    if username not in rooms[room]:
        rooms[room].append(username)
    
    # Отправляем список пользователей всем в комнате
    emit('user_list', {'users': rooms[room]}, room=room)
    
    # Системное сообщение
    timestamp = datetime.datetime.now().strftime("%H:%M")
    emit('status', {
        'msg': f'{username} присоединился к чату', 
        'type': 'system',
        'time': timestamp
    }, room=room)

@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    if room in rooms and username in rooms[room]:
        rooms[room].remove(username)
    emit('user_list', {'users': rooms.get(room, [])}, room=room)
    emit('status', {'msg': f'{username} покинул чат', 'type': 'system'}, room=room)

@socketio.on('send_message')
def on_send_message(data):
    username = data['username']
    room = data['room']
    text = data['text']
    timestamp = datetime.datetime.now().strftime("%H:%M")
    
    emit('receive_message', {
        'username': username,
        'text': text,
        'time': timestamp
    }, room=room)

# --- WebRTC Сигнализация (для видео) ---

@socketio.on('offer')
def on_offer(data):
    emit('offer', data, room=data['room'])

@socketio.on('answer')
def on_answer(data):
    emit('answer', data, room=data['room'])

@socketio.on('candidate')
def on_candidate(data):
    emit('candidate', data, room=data['room'])

if __name__ == '__main__':
    # host='0.0.0.0' делает сервер доступным для внешней сети
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    from pyngrok import ngrok

# Создаем туннель
public_url = ngrok.connect(5000)
print(f"🌐 Твой публичный URL: {public_url}")

# Запускаем сервер
socketio.run(app, host='0.0.0.0', port=5000, debug=False)
