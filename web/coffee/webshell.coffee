window.load_webshell_creds = ->
  $.ajax(type: "GET", cache: false, url: "/api/getsshacct")
  .done (data) ->
    $("#webshell_credentials").html '<p>Username: ' + data['username'] + '    Password: ' + data['password'] + ' | ssh '+ data['username'] + '@shell.picoctf.com</p>'
