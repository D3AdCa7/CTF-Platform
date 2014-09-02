window.handle_new_password_submit = ->
  password = $("#new-pass").val();
  token = window.location.hash.slice(1);
  $.ajax(type: "POST", cache: false, url: "/api/resetpassword", dataType: "json", data: {token: token, newpw: password})
  .done (data) ->
    if data['status'] == 0 then alert_class = "alert-error" else if data['status'] == 1 then alert_class = "alert-success"
    $('#pass_reset_msg').hide().html("<div class=\"alert #{alert_class}\">#{data['message']}</div>").slideDown('normal')
    setTimeout( ->
      $('#pass_reset_msg').slideUp('normal', ->
        $('#pass_reset_msg').html('').show())
    , 3000)
  return false