#
# -*- coding: utf-8 -*-

__author__ = "Collin Petty"
__copyright__ = "Carnegie Mellon University"
__license__ = "MIT"
__maintainer__ = ["Collin Petty", "Peter Chapman"]
__credits__ = ["David Brumely", "Collin Petty", "Peter Chapman", "Tyler Nighswander", "Garrett Barboza"]
__email__ = ["collin@cmu.edu", "peter@cmu.edu"]
__status__ = "Production"


from datetime import datetime
import time
import json
import group
from common import db
from common import cache
from common import esc

import problem
import utilities

ctf_start = utilities.timestamp(datetime(2014, 4, 5, 0))
ctf_end = utilities.timestamp(datetime(2014, 4, 6, 16))
# # For debugging only
# ctf_start = utilities.timestamp(datetime(2014, 04, 01, 00) - datetime.utcnow() + datetime.now())


def get_group_scoreboards(tid):
    """Gets the group scoreboards.

    Because of the multithreaded implementation we rebuild the scoreboard in the aggregator, this call can only
    return a value from cache. This prevents multiple page requests from invoking a scoreboard rebuild simultaneously.
    Get all groups a users is a member of and look for group scoreboards for each of these groups.
    """
    group_scoreboards = []
    groups = group.get_group_membership(tid)
    for g in groups:
        board = cache.get('groupscoreboard_'+g['name'])
        if board is not None:
            group_scoreboards.append(json.loads(board))
    return group_scoreboards


def get_scoreboard(session):
    """Get the public/zju scoreboard
    """
    if 'tid' in session and session['is_zju_user']:
        teams = utilities.get_verified_teams_zju()
        ret = get_teams_scoreboard_cached(teams, 'scoreboard_zju')
    else:
        teams = utilities.get_verified_teams_public()
        ret = get_teams_scoreboard_cached(teams, 'scoreboard_public')

    return ret


def get_teams_scoreboard_cached(teams, cache_key):
    """Gets the cached scoreboard of teams.

    Kind of a hack, tells the front end to look for a static page scoreboard rather than sending a 2000+ length
    array that the front end must parse.
    """
    scoreboard = cache.get(cache_key)
    if scoreboard is None:
        scoreboard = dict()
        problems = problem.load_problems()
        problems = [{
            'pid': p['pid'], 
            'displayname': p['displayname']
        }   for p in problems]
        pids = [p['pid'] for p in problems]
        team_scores = [{
            "teamname": t['teamname'], 
            "score": load_team_score(t['tid']),
            "solved": [pids.index(p) 
                for p in problem.get_solved_problems(t['tid'])]
        }   for t in teams]
        team_scores.sort(key=lambda x: (-x['score']['score'], x['score']['time_penalty']))
        scoreboard['problems'] = problems
        scoreboard['teamname'] = [ts['teamname'] for ts in team_scores]
        scoreboard['score'] = [ts['score']['score'] for ts in team_scores]
        scoreboard['solved'] = [ts['solved'] for ts in team_scores]
        cache.set(cache_key, json.dumps(scoreboard), 60 * 60)
    else:
        scoreboard = json.loads(scoreboard)
    return scoreboard


#def get_scoreboard_public():
#    """Gets the archived public scoreboard.
#
#    Kind of a hack, tells the front end to look for a static page scoreboard rather than sending a 2000+ length
#    array that the front end must parse.
#    """
#    scoreboard = cache.get('scoreboard_public')
#    if scoreboard is None:
#        scoreboard = dict()
#        problems = problem.load_problems()
#        problems = [{'pid': p['pid'], 'displayname': p['displayname']} for p in problems]
#        scoreboard['problems'] = problems
#        verified_teams = utilities.get_verified_teams_public()
#        team_scores = [{
#            "teamname": t['teamname'], 
#            "score": load_team_score(t['tid']),
#            "solved": problem.get_solved_problems(t['tid'])
#        }   for t in verified_teams]
#        team_scores.sort(key=lambda x: (-x['score']['score'], x['score']['time_penalty']))
#        team_scores = [{
#            'teamname': t['teamname'], 
#            'score': t['score']['score'],
#            'solved': t['solved']
#        }   for t in team_scores]
#        scoreboard['teamscores'] = team_scores
#        cache.set('scoreboard_public', json.dumps(scoreboard), 60 * 60)
#    else:
#        scoreboard = json.loads(scoreboard)
#    return scoreboard
#
#
#def get_scoreboard_zju():
#    """Gets the archived public scoreboard.
#
#    Kind of a hack, tells the front end to look for a static page scoreboard rather than sending a 2000+ length
#    array that the front end must parse.
#    """
#    scoreboard = cache.get('scoreboard_zju')
#    if scoreboard is None:
#        scoreboard = dict()
#        problems = problem.load_problems()
#        problems = [{'pid': p['pid'], 'displayname': p['displayname']} for p in problems]
#        scoreboard['problems'] = problems
#        verified_teams = utilities.get_verified_teams_public()
#        team_scores = [{
#            "teamname": t['teamname'], 
#            "score": load_team_score(t['tid']),
#            "solved": problem.get_solved_problems(t['tid'])
#        }   for t in verified_teams]
#        team_scores.sort(key=lambda x: (-x['score']['score'], x['score']['time_penalty']))
#        team_scores = [{
#            'teamname': t['teamname'], 
#            'score': t['score']['score'],
#            'solved': t['solved']
#        }   for t in team_scores]
#        scoreboard['teamscores'] = team_scores
#        cache.set('scoreboard_zju', json.dumps(scoreboard), 60 * 60)
#    else:
#        scoreboard = json.loads(scoreboard)
#    return scoreboard


def load_team_score(tid):
    """Get the score for a team.

    Looks for a cached team score, if not found we query all correct submissions by the team and add up their
    basescores if they exist. Cache the result.
    """
    score = cache.get('teamscore_' + tid)
    if score is None:
        problems = problem.load_problems()
        pscore = {p['pid']: p['basescore'] for p in problems}
        solved = problem.get_solved_problems(tid)
        score = dict()
        score['score'] = sum(pscore[pid] for pid in solved)
        # TODO: calculate time penalty
        submission = list(db.submissions.find(
            {
                "tid": tid, 
                "correct": True,
                "pid": {"$ne": "wait_re"},
                "timestamp": {"$gt": ctf_start},
                "timestamp": {"$lt": ctf_end}
            }, {
                "_id": 0, 
                "pid": 1, 
                "timestamp": 1
            }))
        time_penalty = max([0] + [s['timestamp'] for s in submission])
        score['time_penalty'] = time_penalty
        cache.set('teamscore_' + tid, json.dumps(score), 60 * 60)
    else:
        score = json.loads(score)
    return score


def load_group_scoreboard(group):
    """Build the scoreboard for an entire group of teams.

    Get all of he team names, tid's, and affiliations for all teams that  are a member of the given group.
    Iterate over all of the teams grabbing the last correct submission date (tie breaker). If the last subdate does
    not exist in the cache rebuild it by grabbing all of a teams correct submission and sorting by submission
    timestamp.
    Sort all team score's by their last submission date, we then sort the list by the score. The python sorting
    algorithm is guaranteed stable so equal scores will be ordered by last submission date.
    Cache the entire scoreboard.
    """
    teams = [
        {'tid': t['tid'],
         'teamname': t['teamname'],
         'affiliation': t['affiliation'] if 'affiliation' in t else None}
        for t in list(db.teams.find({'tid': {'$in': group['members']}}, {'tid': 1, 'teamname': 1, 'affiliation': 1}))]
    for t in teams:
        lastsubdate = cache.get('lastsubdate_' + t['tid'])
        if lastsubdate is None:
            subs = list(db.submissions.find({'tid': t['tid'],
                                             'correct': True,
                                             'timestamp': {"$lt": end}}))
            if len(subs) == 0:
                lastsubdate = str(datetime(2000, 01, 01))
            else:
                sortedsubs = sorted(subs, key=lambda k: str(k['timestamp']), reverse=True)
                lastsubdate = str(sortedsubs[0]['timestamp'])
            cache.set('lastsubdate_' + t['tid'], lastsubdate, 60 * 30)
        t['lastsubdate'] = lastsubdate

    teams.sort(key=lambda k: k['lastsubdate'])
    top_scores = [x for x in sorted(
        [{'teamname': esc(t['teamname']),
          'affiliation': esc(t['affiliation']),
          'score': load_team_score(t['tid'])}
         for t in teams], key=lambda k: k['score'], reverse=True) if x['score'] > 0]
    cache.set('groupscoreboard_' + group['name'], json.dumps({'group': group['name'], 'scores': top_scores}), 60 * 30)
