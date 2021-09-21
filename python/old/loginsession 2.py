from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, validators
from wtforms.validators import DataRequired, Length, Regexp
from flask_session import Session
from flask_socketio import SocketIO, send, emit, disconnect
from pythonosc import udp_client

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = 'secret!'
Session(app)

socketio = SocketIO(app, manage_session=False, cors_allowed_origins="*")

class LoginForm(FlaskForm):
   username = StringField('username', validators=[DataRequired(), Length(min=4, max=32)])

## Store logged in users in a dictionary

connected_users = dict()

@app.route('/', methods=['GET', 'POST'])
def login():
   global connected_users

   new_sid = session.sid
   session['sid'] = new_sid

   for sid in connected_users.keys():
      if sid == session['sid']:
         print("User SID exists, redirect!")
         return redirect(url_for('chat'))

   form = LoginForm()
   if form.validate_on_submit():

      username = form.username.data

      new_user = username
      new_ip = request.remote_addr

      session['username'] = new_user
      session['remote_ip'] = new_ip

      connected_users[new_sid] = {'username': new_user, 'remote_ip' : new_ip}

      return redirect(url_for('.chat'))

   return render_template('index.html', form=form)

@app.route('/chat')
def chat():
   global connected_users
   print("User logged in, connected users are: ", connected_users)
   for sid in connected_users.keys():
      print (connected_users[sid]['username'])
   return render_template('chat.html')

@app.route('/log_out')
def log_out():
   global connected_users
   connected_users.pop(session['sid'], '')
   session.clear()
   print("User logged out, connected users are: ", connected_users)
   return redirect(url_for('login'))

## Socket functions

previous_messages = []

def storeMessages(msg):
   previous_messages.append(msg)

def appendMessage(msg):
   ## print('Appended message from ', msg['user'], 'to list: ', msg['string'])
   emit('append-message', msg, broadcast=True)

## Sockets

@socketio.on('chat-message')
def chatMessage(msg):
   name = session['username']
   remote_ip = session['remote_ip']

   msg_payload = {'username':name,'remote_ip':remote_ip,'message':msg}

   appendMessage(msg_payload)
   storeMessages(msg_payload)
   print(msg)

@socketio.on('connect')
def connect():
   print("connected!")

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0')
