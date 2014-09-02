handle_teamname_lookup_submit = ->
  $.ajax(type: "POST", cache: false, url: "/api/lookupteamname", dataType: "json", data: {email: $('#forgot-email').val()})
  .done (data) ->
    frgt_msg_div = $ '#forgot_msg'
    if data['status'] == 0 then alert_class = 'alert-error' else if data['status'] == 1 then alert_class = 'alert-success'
    frgt_msg_div.hide().html('<div class="alert ' + alert_class + '">' + data['message'] + '</div>').slideDown('normal')
    setTimeout( ->
      frgt_msg_div.slideUp('normal', ->
        frgt_msg_div.html('').show())
    , 4000)
  return false