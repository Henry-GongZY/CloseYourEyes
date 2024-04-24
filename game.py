from flask import Flask, render_template, session, redirect, url_for, request
from flask_socketio import SocketIO, emit
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Use a secure key

socketio = SocketIO(app)

# 存储玩家信息
players = {}
@app.route('/')
def index():
    return render_template('index.html', num_players=len(session.get('identities', [])))

@app.route('/start', methods=['POST'])
def start_game():
    num_players = int(request.form.get('num_players', 5))
    identities = ['Thief'] + ['Rat'] * (num_players - 1)
    random.shuffle(identities)
    dice = [random.randint(1, 6) for _ in range(num_players)]

    # 分配玩家 ID 和存储信息
    session['players'] = {}
    for i in range(num_players):
        session['players'][i] = {'identity': identities[i], 'dice': dice[i]}

    # 触发开始游戏的事件
    socketio.emit('start_game', {}, broadcast=True)
    return '', 204

@app.route('/night')
def night():
    player_id = request.args.get('player_id', type=int)
    if player_id in session['players']:
        player_info = session['players'][player_id]
        return render_template('night.html', identity=player_info['identity'], dice=player_info['dice'])
    else:
        return redirect(url_for('index'))

@app.route('/wake', methods=['POST'])
def wake():
    dice_number = int(request.form['dice_number'])
    active_players = [i for i, dice_val in enumerate(session.get('dice')) if dice_val == dice_number]
    context = {}
    if len(active_players) == 1 and session['identities'][active_players[0]] == 'Rat':
        target_player = int(request.form.get('target_player'))
        context = {'target_dice': session['dice'][target_player]}
    return render_template('wake.html', context=context, active_players=active_players)

@app.route('/day')
def day():
    thief_id = int(request.args.get('thief_id'))
    accomplice_id = int(request.args.get('accomplice_id'))
    session['accomplice_id'] = accomplice_id
    return render_template('day.html', thief_id=thief_id, accomplice_id=accomplice_id)

@app.route('/end')
def end_game():
    session.clear()
    return redirect(url_for('index'))


@socketio.on('connect')
def on_connect():
    print('Client connected')

@socketio.on('disconnect')
def on_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    socketio.run(app, debug=True)
