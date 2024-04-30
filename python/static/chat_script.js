$(document).ready(function() { // Flytta helt enkelt den hr frn document ready till en login-knapp?

    var socket = io.connect('http://' + document.domain + ':' + location.port); // Snyggare

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

    socket.on('check_disconnect', function(uuid){
        socket.emit('destroySocket', localStorage.getItem('sessionID'))
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

    // Display command and/ or command errors: user feedback

    socket.on('show-command', function(key) {
        $("#errors").html(key)
    });

    // en funktion för att appenda till chatlistan

    socket.on('append-message', function(msg) {

        $("#message-list").append('<li><span id ="message-info">'+msg.username+'['+msg.timestamp+ ']</span>'+msg.message+ '</li>');
        $("#messages-container").animate({ scrollTop: $('#messages-container').prop("scrollHeight")}, 1000);
    });

    $('#chat-form').submit(function(){
        socket.emit('chat-message', $('#chat-input').val()); // Gör om till ett json-objekt !
        $('#chat-input').val('');
        return false;
    });

});
