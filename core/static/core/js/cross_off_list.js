function cross_off_list(id) {
    var checked = document.getElementById("attendance_checkbox_" + id).checked;
    var elem = document.getElementById("list_row_" + id);
    if (checked) {
        elem.style.textDecoration = "line-through";
        elem.classList.add("table-danger");
    } else {
        elem.style.textDecoration = "none";
        elem.classList.remove("table-danger");
    }
}