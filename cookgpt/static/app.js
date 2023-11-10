$(() => {
    var socket = io.connect();
    socket.on('connect', () => {
        console.log('connected');
        socket.emit('my event', {data: 'I\'m connected!'});
    });
});