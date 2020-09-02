var text_max = 500;
$('#char_count').html('0 / ' + text_max );

$('#text_char_count').keyup(function() {
  var text_length = $('#text_char_count').val().length;
  var text_remaining = text_max - text_length;
  
  $('#char_count').html(text_length + ' / ' + text_max);
});