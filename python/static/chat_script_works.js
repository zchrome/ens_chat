$(document).ready(function() { // Flytta helt enkelt den hr frn document ready till en login-knapp?

    // Tror ev inte att det spelar nån roll
    // Men rigga upp routes som för över sessionen?

    var socket = io.connect('http://' + document.domain + ':' + location.port); // Snyggare
    // var socket = io.connect('http://127.0.0.1:5000');

    var sessionID = localStorage.getItem('sessionID');
    console.log(sessionID);

    // scroll to bottom on connect

    $('#messages-container').scrollTop($('#messages-container')[0].scrollHeight);

    socket.emit('serverCheckSession', sessionID)

    socket.on('check_session', function(uuid){
        if (uuid != sessionID) {
            console.log("Not equal");
            localStorage.setItem("sessionID", uuid);
            socket.emit('newUser', uuid)
        } else {
            console.log("Equal");
        }
    });

    socket.on('connect', function() {
        socket.emit('userCheckConnection', socket.id);
    });

    socket.on('session', function(flask_sid, flask_name) {
        socket.userID = flask_name;
        // console.log(flask_sid)
        localStorage.setItem("sessionID", flask_sid);
        console.log(localStorage.getItem("sessionID"));
        console.log(socket.userID);
    });

    // socket.on('connect', function() {
    //    socket.emit('joined', {});
    //    });

    // en funktion för att appenda till chatlistan

    socket.on('append-message', function(msg) {

        // $("#message-list").append('<li>'+msg+'</li>');
        $("#message-list").append('<li>' +msg.username+ '@' +msg.remote_ip+ ': ' +msg.message+ '</li>');
        // Oklart om nedan funkar på Chrome?
        $("#messages-container").animate({ scrollTop: $('#messages-container').prop("scrollHeight")}, 1000);
        // Spara under, den animerar inte så ev bättre:
        // $('#messages-container').scrollTop($('#messages-container')[0].scrollHeight);
    });

    $('#chat-form').submit(function(){
        socket.emit('chat-message', $('#chat-input').val()); // Gör om till ett json-objekt !
        // socket.send('message', $('#chat-input').val()); // hur kunde det bli så fel
        $('#chat-input').val('');
        return false;
    });

});
