fields = ['email', 'team', 'name', 'aff', 'pass']

clear = ->
  $('#reg-'+field).val('') for field in fields.concat ['group']
  $('#reg_group_vis_toggle').slideUp('fast');
  $('#join-button').fadeOut('fast', -> $('#register-button').fadeIn('fast'))

getRegData = ->
  post = {}
  post[field] = $('#reg-'+field).val() for field in fields.concat ['group']
  return post

$(document).ready ->
  $('#reg-email').focus()
  $('#register-button').click (event) ->
    $.ambiance({message: "正在尝试发送验证邮件, 请稍候.", type: 'success', timeout: 10})
    event.preventDefault()
    hash = window.location.hash
    post = getRegData()
    if post['group'] == '' and hash.indexOf("#") != -1 then post['group'] = hash.substring(hash.indexOf("#")+1); post['joingroup'] = 'true'
    $.ajax(type: 'POST', url: '/api/register', dataType: 'json', data: post)
    .done (data) ->
      if data['status'] == 0
        $.ambiance({message: data['message'], type: 'error', timeout: 10})
      else if data['status'] == 1
        $.ambiance({message: data['message'], type: 'success', timeout: 7})
        clear()
      else if data['status'] ==2
        $.ambiance({message: data['message'], timeout: 5})
        $('#register-button').fadeOut('fast', -> $('#join-button').fadeIn('fast'))
        for field in fields.concat ['group']
          $('#reg-'+field).change ->
            for field in fields.concat ['group']
              $('#reg-'+field).unbind 'change'
            $('#join-button').fadeOut('fast', -> $('#register-button').fadeIn('fast'))

  $('#create_group_link').click (event)->
    event.preventDefault()
    $('#reg_group_vis_toggle').slideDown('fast')

  $('#join-button').click (event) ->
    event.preventDefault()
    post = getRegData()
    post['joingroup'] = 'true'
    $.ajax(type: 'POST', url: '/api/register', dataType: 'json', data: post)
    .done (data) ->
      if data['status'] == 0
        $.ambiance({message: data['message'], type: 'error', timeout: 10})
      else if data['status'] == 1
        $.ambiance({message: data['message'], type: 'success', timeout: 5})
        clear();



