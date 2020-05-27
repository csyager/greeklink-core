function filter_list() {
    var input, filter, table, tr, td, i, txtValue;
    input = document.getElementById("social_search");
    filter = input.value.toUpperCase();
    table = document.getElementById("list_table");
    tr = table.getElementsByTagName("tr");

    for (i = 1; i < tr.length; i++) {
        td = tr[i].getElementsByTagName("td")[0];
        if (td) {
            txtValue = td.textContent || td.innerText;
            if (txtValue.toUpperCase().indexOf(filter) > -1) {
                tr[i].style.display = "";
            } else {
                tr[i].setAttribute('style', 'display:none !important');
            }
        }
    }
}