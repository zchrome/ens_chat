$(document).ready(function() { // Flytta helt enkelt den hr frn document ready till en login-knapp?

    // Tror ev inte att det spelar nån roll
    // Men rigga upp routes som för över sessionen?

    // var socket = io.connect('http://' + document.domain + ':' + location.port); // Snyggare
    var socket = io.connect('http://127.0.0.1:5000');

    socket.on('connect', function() {
        socket.emit('joined', {});
        });

    // en funktion för att appenda till chatlistan

    socket.on('message', function(msg) {
        $("#message-list").append('<li>'+msg+'</li>');
        // $('#chat-window').animate({scrollTop: $('#message-list').prop("scrollHeight")}, 1000);
    });

    $('#chat-form').submit(function(){
        socket.send($('#chat-input').val());
        // socket.send('message', $('#chat-input').val()); // hur kunde det bli så fel
        $('#chat-input').val('');
        return false;
    });

});
