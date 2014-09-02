hint_panel = (hint) ->
  if (hint != "") then """
    <div class="panel panel-info">
      <div class="panel-heading">
        提示
      </div>
      <div class="panel-body">
        #{hint}
      </div>
    </div>"""
  else
    ""

window.load_problems = ->
  $.ajax(type: "GET", cache: false, url: "/api/problems", dataType: "json")
    .done (data) ->
      categories = ['WEB', 'EXPLOIT', 'REVERSE', 'CRYPTO', 'MISC']
      label_names = ['primary', 'success', 'info', 'warning', 'danger']
      for d in data
        id = d['pid']
        for i in [0..4]
          if categories[i] == d['category']
            label_name = label_names[i]
            break

        $("#problems-accordion").append """
          <div class="panel panel-default">
            <div class="panel-heading">
              <h4 class="panel-title">
                <a data-toggle="collapse" data-parent="#problems-accordion" href="#problem-#{id}" class="problem-title">
                  #{if d['correct'] then "<span id=\"problem-status-#{id}\" class=\"solved\">[已解决]</span>" else "<span id=\"problem-status-#{id}\" class=\"unsolved\">[未解决]</span>"}
                  #{d['displayname']}
                  <div class="pull-right">
                    <span class="label label-default">#{d['basescore']}</span>
                    <span class="category-label label label-#{label_name}">#{d['category']}</span>
                  </div>
                </a>
              </h4>
            </div>
            <div id="problem-#{id}" class="panel-collapse collapse">
              <div class="panel-body">
                <p>
                  #{d['desc']}
                </p>
                #{hint_panel(d['hint'])}

                <hr>
                <div class="flag-panel">
                  <form onsubmit="javascript:return false;" class="flag-form">
                  """ +
                      # <div class="recaptcha-container form-group" id="recaptcha-#{id}"></div>
                  """
                      <div class="form-group">
                        <input name="flag" id="#{id}" type="text" class="form-control flag-input" placeholder="FLAG">
                      </div>
                      <button class="btn btn-primary pull-right" type="submit">提交!</button>
                  </form>
                </div>
              </div>
            </div>
          </div>"""
        ###
        $("#problem-#{id}").on "show.bs.collapse", ()->
          $(this).find(".recaptcha-container").hide().show(300)
          rid = $(this).find(".recaptcha-container").attr("id")
          $(".recaptcha-container").empty()
          $(this).find(".recaptcha-container").html """
            <div onClick="javascript:Recaptcha.reload()" title="点击图片以切换验证码" id="recaptcha_image" data-toggle="tooltip" data-placement="bottom"></div>
            <input type="text" id="recaptcha_response_field" name="recaptcha_response_field" class="form-control" placeholder="CAPTCHA" />
            """
          $("#recaptcha_image").tooltip()
          Recaptcha.destroy()
          Recaptcha.create(
            "6LcPFPESAAAAALdVWq62jvJ3HEEBvkcOfUOSZ9PV",
            rid,
            {
              theme: "custom",
              custom_theme_widget: "#{rid}"
            }
          )
        ###
      $(window.location.hash).collapse("show");
      $("form").each () ->
        $(this).validate
          "rules":
            # "recaptcha_response_field":
            # required: true
            flag:
                required: true
          submitHandler: (form) ->
            handle_submit($(form).find("input[name=flag]").attr("id"))
          highlight: (element) ->
            $(element).closest('.form-group').removeClass('has-success').addClass('has-error');
          unhighlight: (element) ->
            $(element).closest('.form-group').removeClass('has-error').addClass('has-success');

