

var country, cities, newEvent, eventCome, messages,
    fields = ['name', 'email', 'phone', 'country', 'city','birth'];

$(document).ready(function(){

    newEvent = $('#modal-template');
    eventCome = $('#alert-template');
    messages = $('#messages');

    $("#datepicker").datepicker({
        onSelect: function(date) {
            var time = $('#eventTime'),
                date_ = $('#eventDate');

            $('#eventId').val('');
            date_.val(date);
            date_.prop('disabled', true);
            time.val('');
            time.inputmask('99:99');
            $('#eventText').val('');

            $('#saveBtn').show();
            $('#editBtn').hide();

            newEvent.modal('show');
        }
    });

    $('[name="birth"]').datepicker();

    country = $('[name="country"]');
    cities = $('[name="city"]');

    getProfileData();

    country.on('change', function(){
        getCities(country.val());
    });

    // get event list
    getEvents();
});

function getEvents(){
    $.get('/get-events', {}, function(data){

        var data = JSON.parse(data);

        messages.empty();

        $.each(data, function(i, ev){
            messages.append(
               '<tr><td class="col-sm-1">' +
               '<a href="javascript:void(null);" onclick="editEvent('+ ev.id +')">' +
               '<i class="glyphicon glyphicon-pencil"></i></a>' +
               '</td><td class="col-sm-8">'+ ev.text +
               '</td><td class="col-sm-2">'+ ev.date +
               '</td><td class="col-sm-1">'+ ev.time +
               '</td></tr>'
           );
        });
    });
}

function addEvent(){
    $.post('/add-event', {
            eventDate: $('#eventDate').val(),
            eventTime: $('#eventTime').val(),
            eventText: $('#eventText').val()
        }, function(res){

            newEvent.modal('hide');
        }
    );
}

function editEvent(id){
    $.get('/edit-event', {'eventId': id}, function(data){

            var data = JSON.parse(data),
                time = $('#eventTime'),
                date = $('#eventDate');

            $('#eventId').val(data.id);
            date.val(data.date);
            date.prop('disabled', false);
            date.datepicker();
            time.val(data.time);
            time.inputmask('99:99');
            $('#eventText').val(data.text);
            $('#saveBtn').hide();
            $('#editBtn').show();

            newEvent.modal('show');
        }
    );
}

function correctEvent(){
    $.post('/edit-event', {
            eventId: $('#eventId').val(),
            eventDate: $('#eventDate').val(),
            eventTime: $('#eventTime').val(),
            eventText: $('#eventText').val()
        }, function(res){

            newEvent.modal('hide');
            getEvents();
        }
    );
}

function closeEvent(){
    newEvent.modal('hide');
}

function closeEvent2(){
    eventCome.modal('hide');
}

function getCities(country_id, info){
    $.get('/get-cities',{'country_id': country_id}, function(res){

        cities.find('option').remove();

        $.each(JSON.parse(res), function(key, value) {
            cities
            .append($("<option></option>")
            .attr("value",key)
            .text(value));
        });

        if(info){
            $.each(fields, function(ind, el){
                $('[name='+el+']').val(info[el]);
            });
        }

    });
}


function getProfileData(){
    $.get('/get-profile', {}, function(res){

        var info = JSON.parse(res);

        if(info.photo){
            $('img').attr('src', info.photo);
        }
        delete info.photo;

        if($.isEmptyObject(info)){
            getCities(country.val());
        }
        else{
            getCities(info['country'], info);
        }
        setDisabled(true);
    });
}


var requiredText = 'Обязательное поле для заполнения';

function submitForm(){
    var f = $('#profileForm'),
        validator = f.data('validator');

    f.validate({
        rules: {
            name: {
                required: true
            },
            email: {
                required: true,
                email: true
            },
            phone: {
                required: true,
                minlength: 11
            }
        },
        messages: {
            name: {
                required: requiredText
            },
            email: {
                email: "Пожалуйста, введите коректный e-mail",
                required: requiredText
            },
            phone: {
                required: requiredText,
                minlength: "Пожалуйста введите 11 цифр"
            }
        }
    });
    if(!f.valid()){
        return;
    }

    var params = new FormData(f[0]);
    $.ajax({
        url: '/',
        data: params,
        processData: false,
        contentType: false,
        type: 'POST',
        success: function(res){
            setDisabled(true);
        }
    });
}

function editForm(){
    setDisabled(false);
}

function cancelEdit(){
    getProfileData();
}

function setDisabled(flag){
    $.each(fields, function(ind, el){
        $('[name='+el+']').prop('disabled', flag);
    });
    $('#submit').prop('disabled', flag);
    $('#cancel').prop('disabled', flag);
    $('#edit').prop('disabled', !flag);
}

function logout(){

}

