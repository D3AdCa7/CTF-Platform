display_progress = (problems, solved) ->
  progress_html = "<ul class=\"scoreboard-progress\">"
  for i in [0...problems.length]
    problem = problems[i]
    progress_html += """
      <li>
        <a target="_blank" href="/problems#problem-#{problem["pid"]}" class="progress-bullet #{if i in solved then "solved" else "unsolved"}" data-toggle="tooltip" data-placement="bottom" title="#{problem["displayname"]}"></a>
      </li>"""
  progress_html += "</ul>"


fill_scoreboard = (problems, teamname, solved, score, start_idx) ->
    fill_interval = 16
    end_idx = Math.min(start_idx + fill_interval, teamname.length)
    setTimeout () ->
        for i in [start_idx...end_idx]
            progress_html = display_progress problems, solved[i]
            $("#scoreboard-table").append """
                <tr>
                    <td>#{i}</td>
                    <td>#{teamname[i]}</td>
                    <td>#{progress_html}</td>
                    <td>#{score[i]}</td>
                </tr>"""
            i++
        setTimeout () -> fill_scoreboard(problems, teamname, solved, score, end_idx)
    $(".progress-bullet").tooltip()
    return 


window.load_scoreboards = ->
  $.ajax(type: "GET", cache: false, url: "/api/scoreboards", dataType: "json", async: true)
  .done (data) ->
    problems = data["problems"]
    teamname = data["teamname"]
    solved = data["solved"]
    score = data["score"]
    fill_scoreboard(problems, teamname, solved, score, 0)
    ###
    setTimeout () -> 
      for i in [0...teamname.length]
        progress_html = display_progress problems, solved[i]
        $("#scoreboard-table").append """
          <tr>
            <td>#{i}</td>
            <td>#{teamname[i]}</td>
            <td>#{progress_html}</td>
            <td>#{score[i]}</td>
          </tr>"""
        i++
    ###
    $(".progress-bullet").tooltip()
