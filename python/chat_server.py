import re, uuid
from datetime import datetime
from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, validators
from wtforms.validators import DataRequired, Length, Regexp, ValidationError
from flask_session import Session
from flask_socketio import SocketIO, send, emit, disconnect
from pythonosc import udp_client

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = 'secret!'
Session(app)

socketio = SocketIO(app, manage_session=False, cors_allowed_origins="*")

now = datetime.now();
time = now.strftime("%H:%M:%S")

## Store logged in users in a dictionary

connected_users = dict()

class LoginForm(FlaskForm):
   username = StringField('username', validators=[DataRequired(), Length(min=4, message=("Username must be at least for characters!"))])
   def validate_username(form, field):
      for c_user in connected_users.values():
         if field.data in c_user.values():
               raise ValidationError("Username already in use...")

@app.route('/', methods=['GET', 'POST'])
def login():
   global connected_users

   new_sid = session.sid
   session['sid'] = new_sid
   session['logged_in'] = False

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
      session['logged_in'] = True
      session['uuid'] = str(uuid.uuid4())

      connected_users[new_sid] = {'username': new_user, 'remote_ip' : new_ip, 'uuid': session['uuid']}

      return redirect(url_for('.chat'))

   return render_template('index.html', form=form)

previous_messages = []

@app.route('/chat')
def chat():
   if session['sid'] in connected_users.keys():

      session['connection_id'] = str(uuid.uuid4())

      print(session['connection_id'])

      print("Yes user was there!")
      print("User logged in, connected users are: ", connected_users)
      for sid in connected_users.keys():
         print (connected_users[sid]['username'])
      return render_template('chat.html', previous_messages=previous_messages)
   return redirect(url_for('login'))

@app.route('/log_out')
def log_out():
   global connected_users
   connected_users.pop(session['sid'], '')
   session.clear()
   print("User logged out, connected users are: ", connected_users)
   return redirect(url_for('login'))

@socketio.event
def connect():
   emit('check_session', session['uuid'])

@socketio.event
def newUser(uuid):
   name = session['username']
   remote_ip = session['remote_ip']
   msg_payload = {'timestamp': time, 'username':name,'remote_ip':remote_ip, 'message': " has connected."}
   appendMessage(msg_payload)
   storeMessages(msg_payload)

@socketio.event
def disconnect():
   print("someone disconnected...")
   emit('check_disconnect', session['uuid'])

@socketio.event
def destroySocket(uuid):
   print('got dstry socket event', uuid)
   if session['uuid'] != uuid:
      name = session['username']
      remote_ip = session['remote_ip']
      msg_payload = {'timestamp': time, 'username':name,'remote_ip':remote_ip, 'message': " has DISconnected."}
      appendMessage(msg_payload)
      storeMessages(msg_payload)

## Socket functions

def storeMessages(msg):
   previous_messages.append(msg)

def appendMessage(msg):
   ## print('Appended message from ', msg['user'], 'to list: ', msg['string'])
   emit('append-message', msg, broadcast=True)


def sendCollider(msg, remote_ip):
   local_collider = udp_client.SimpleUDPClient(remote_ip, 57120);
   local_collider.send_message("/reply", msg)

## En OSC-def för varje event?

def findUser(msg):
   pattern = re.compile('@\w+')
   found_users = re.findall(pattern, msg)
   for user in found_users:
      user = user.translate({ord('@'): None})
      for c_user in connected_users.values():
         if user in c_user.values():
            if user == session['username']:
               print("You can't send messages to urself!!")
            else:
               print("Found user ", user, "with IP: ", c_user['remote_ip'])
               return c_user['remote_ip']
               ## sendCollider(msg, c_user['remote_ip'])
         else:
            print("Found no matching user")

class ColliderClient:
   # Instansiering...
   def __init__(self, remote_ip):
      self.local_collider = udp_client.SimpleUDPClient(remote_ip, 57120)
      self.pattern = re.compile('-?(?:\d+,?)+')
      # self.pattern = re.compile('[0-9]+')

   def send_message(self, msg):
      for key in keyword_dictionary:
         if key in msg:
            integers = re.findall(self.pattern, msg)
            self.local_collider.send_message(key, tuple(integers))
            print(key, msg)

class sendToUser:
   def __init__(self):
      self.pattern = re.compile('@\w+')

   def send_message(self, msg):
      user_in_message = re.findall(self.pattern, msg)
      for user in user_in_message:
         user = user.translate({ord('@'): None})
         for c_user in connected_users.values():
            if user in c_user.values():
               # print("found a user")
               if user == session['username']:
                  print("You can't send messages to urself!!")
               else:
                  print("Found user ", user, "with IP: ", c_user['remote_ip'])
                  collider_client = ColliderClient(c_user['remote_ip'])
                  collider_client.send_message(msg)
            else:
               print("Found no matching user")

def send_all(msg):
   for c_user in connected_users.values():
      local_collider = udp_client.SimpleUDPClient(c_user['remote_ip'], 57120)
      local_collider.send_message("/command_word", msg)

command_dictionary = {"lol", "wow", "omg", "lmao", ":)", ":(", "xD", "wtf", "haha", "how do you turn this on"}

keyword_dictionary = {"/seq":"a sequence", "/drone": "a drone", "/stop": "a stop", "/tempo" : "a tempo"}

def process_keyword(msg):
   for key in keyword_dictionary:
      if key in msg:
         socketio.emit('show-command', key)
         print(keyword_dictionary[key])
      else:
         socketio.emit('show-error')

def process_command(msg):
   for command in command_dictionary:
      if command in msg:
         socketio.emit('show-command', command)
         send_all(msg)

## Sockets

@socketio.on('chat-message')
def chatMessage(msg):
   name = session['username']
   remote_ip = session['remote_ip']

   msg_payload = {'timestamp': time, 'username':name,'remote_ip':remote_ip,'message': ': ' +msg}

   appendMessage(msg_payload)

   target_user = sendToUser()
   target_user.send_message(msg)


   storeMessages(msg_payload)
   process_command(msg)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0')
