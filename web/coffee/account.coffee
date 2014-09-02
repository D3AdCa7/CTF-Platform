window.load_group_memberships = ->
  $.ajax(type: 'GET', dataType: 'json', url: '/api/groups')
  .done (data) ->
    html = "<div class=\"control-group\">"
    if data.length == 0 
      html+= """<p class="text-info">You are currently not a member of any groups.</p>"""
    else
      for g in data
        if g['owner'] == true then permission = 'owner' else permission = 'member'
        html += """<div class="controls #{permission}" id="gid_#{g.id}">#{g.name}<div class="close remove-group-button">&times;</div></div>"""
    html += "</div>"
    $('#group_membership_table').html html
    $('.remove-group-button').click (event) -> leave_group $(this).parent()

window.submit_new_group_membership = ->
  $.ajax(type: 'POST', dataType: 'json', url: '/api/joingroup', data: {name: $('#group_join_input').val()})
  .done (data) ->
    if      data['status'] == 0 then msg_class = 'error'
    else if data['status'] == 1 then msg_class = 'success'; load_group_memberships();
    else if data['status'] == 2 then msg_class = 'default'
    else if data['status'] == 3
      msg_class = 'default'
    $.ambiance(message: data['message'], type: msg_class, timeout: 3)

window.create_new_group = ->
  $.ajax(type: 'POST', dataType: 'json', url: '/api/creategroup', data: {name: $('#group_join_input').val()})
  .done (data) ->
    if      data['status'] == 0 then msg_class = 'error'
    else if data['status'] == 1 then msg_class = 'success'; load_group_memberships();
    else if data['status'] == 2
      msg_class = 'default'
      $('#create-group-button').fadeOut('fast', -> $('#join-group-button').fadeIn('fast'))
    $.ambiance(message: data['message'], type: msg_class, timeout: 3)

window.submit_new_password = ->
  $.ajax(
    type: 'POST',
    dataType: 'json',
    url: '/api/updatepass',
    data: {pwd: $('#new-pass').val(), conf: $('#conf-pass').val()})
  .done (data) ->
    if      data['status'] == 0 then msg_class = 'error';
    else if data['status'] == 1 then msg_class = 'success'
    $.ambiance(message: data['message'], type: msg_class, timeout: 3)
    $('#new-pass').val(''); $('#conf-pass').val('');

window.leave_group = (div) ->
  console.log div.attr('id')
  $.ajax(type: 'POST', dataType: 'json', url: '/api/leavegroup', data: {gid: div.attr('id').replace('gid_', '')})
  .done (data) ->
    if      data['status'] == 0 then msg_class = 'error'
    else if data['status'] == 1 then msg_class = 'success'; load_group_memberships();
    $.ambiance(message: data['message'], type: msg_class, timeout: 3)

$(document).ready ->
  $('#join-group-button').click (event) ->
    event.preventDefault()
    submit_new_group_membership()
    return false
  $('#create-group-button').click (event) ->
    event.preventDefault()
    create_new_group()
    return false
  $('#update-password-button').click (event) ->
    event.preventDefault()
    submit_new_password()
    return false
