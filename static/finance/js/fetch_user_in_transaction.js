function fetchUsers(transaction_id) {
    $.ajax({
        url: 'get_users_in_transaction' + transaction_id,
        data: {},
        success: function(data) {
            data = JSON.parse(data);
            var optionsAsString = ""
            for (var key in data) {    
                var value = data[key];
                optionsAsString += "<option value='" + key + "'>" + value + "</option>";
            }
            if (Object.keys(data).length==0){
                document.getElementById('payment_with_transaction_user_select').style.display = 'none';
                document.getElementById('id_user_label').style.display = 'none';
                document.getElementById('payment_with_transaction_amount').style.display = 'none';
                document.getElementById('id_amount_label').style.display = 'none';
            } else {
                document.getElementById('payment_with_transaction_user_select').style.display = 'block'
                document.getElementById('id_user_label').style.display = 'block';
                document.getElementById('payment_with_transaction_amount').style.display = 'block'
                document.getElementById('id_amount_label').style.display = 'block';
            }
            document.getElementById("payment_with_transaction_user_select").innerHTML = optionsAsString;
        }
    });
}