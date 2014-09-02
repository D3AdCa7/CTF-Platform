window.load_compete = ->
  $.getScript("compete/game.min.js", ->
    $.getScript("compete/lib/API.js", ->
      $.getScript("compete/lib/jquery-ui.js", ->
        $.getScript("compete/lib/hintinit.js"))))
