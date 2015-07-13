

var ws = new WebSocket("ws://127.0.0.1:8888/socket");
console.log(ws);

ws.onopen = function(){
   console.log('onopen');
};

ws.onmessage = function (evt){
    console.log('onmessage');

    try{
        var data = JSON.parse(evt.data);
        messages.append(
            '<tr><td class="col-sm-1">' +
            '<a href="javascript:void(null);" onclick="editEvent('+ data.id +')">' +
            '<i class="glyphicon glyphicon-pencil"></i></a>' +
            '</td><td class="col-sm-8">'+ data.text +
            '</td><td class="col-sm-2">'+ data.date +
            '</td><td class="col-sm-2">'+ data.time +
            '</td></tr>'
        );
        $('#comeEventDate').val(data.date);
        $('#comeEventTime').val(data.time);
        $('#comeEventText').val(data.text);
        eventCome.modal('show');

    }
    catch(err){
       console.log(err);
    }
};

ws.onclose = function(){
   console.log('onclose');
};