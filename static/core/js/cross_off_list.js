function cross_off_list(id) {
    var checkbox = document.getElementById("attendance_checkbox_" + id);
    var elem = document.getElementById("list_row_" + id);

    $.ajax({
        url: "check_attendee",
        data: {
            'attendee_id': id,
        },
        dataType: 'json',
        success: function (data) {
            if (data.attended) {
                elem.style.textDecoration = "line-through";
                elem.classList.add("table-danger");
                checkbox.checked = true;
            } else {
                elem.style.textDecoration = "none";
                elem.classList.remove("table-danger");
                checkbox.checked = false;
            }
        }
    });
}

function refresh_list() {
    var url = window.location.href;
    var event_id = url.substr(url.length-1);
    $.ajax({
        url: "refresh_attendees",
        data: {
            'event_id': event_id,
        },
        success: function(data) {
            for (var key in data) {
                var value = data[key];
                console.log("key: " + key + ", value: " + value);
                document.getElementById('attendance_checkbox_' + key).checked = value;
                if (value) {
                    document.getElementById('list_row_' + key).style.textDecoration = "line-through";
                    document.getElementById('list_row_' + key).classList.add("table-danger");
                } else {
                    document.getElementById('list_row_' + key).style.textDecoration = "none";
                    document.getElementById('list_row_' + key).classList.remove("table-danger");
                }
            }
        }
    });
    setTimeout(refresh_list, 5000);
}

$(document).ready(function() {
    setTimeout(refresh_list, 5000);
});