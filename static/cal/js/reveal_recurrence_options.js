$("#recurring_selection").change(function() {
    if ($(this).val() == 'None'){
        $("#recurrence_options_div").collapse('hide');
        $("#id_start_date").removeAttr('required', '');
    } else {
        $("#recurrence_options_div").collapse('show');
        $("#id_start_date").attr('required', '');
    }
});