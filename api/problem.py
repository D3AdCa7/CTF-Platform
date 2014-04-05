#
# -*- coding: utf-8 -*-

__author__ = "Collin Petty"
__copyright__ = "Carnegie Mellon University"
__license__ = "MIT"
__maintainer__ = ["Collin Petty", "Peter Chapman"]
__credits__ = ["David Brumely", "Collin Petty", "Peter Chapman", "Tyler Nighswander", "Garrett Barboza"]
__email__ = ["collin@cmu.edu", "peter@cmu.edu"]
__status__ = "Production"

import json
import imp
import os
from os.path import basename
from stat import *

from common import db
from common import cache
from pymongo.errors import DuplicateKeyError
from datetime import datetime

import captcha
import utilities


root_web_path = ""
relative_auto_prob_path = ""

auto_generators = dict()


#def load_autogenerators():
#    """Pre-fetch all autogenerators
#
#    Pulls all problems from mongo where 'autogen' == True and then passes them one by one to load_autogenerator(p).
#    """
#    print "Loading autogenerators"
#    for prob in list(db.problems.find({'autogen': True})):
#        if load_autogenerator(prob) is None:
#            print "ERROR - load_autogenerator(prob) returned None for pid: " + prob['pid']
#
#
#def load_autogenerator(prob):
#    """Loads an auto-generator from disk.
#
#    Determines if the passed 'prob' variable is a problem dict from the db or simply a 'pid'. If it is a 'pid' the
#    corresponding prob dict is queried. The generator code specified in the db is then loaded from disk and added
#    to the table of generators if it has a callable 'generate' function. If the generator has a callable
#    'validate_dependencies' function it is called prior to insertion.
#    """
#    if 'pid' not in prob:  # Prob is a 'pid', not a 'prob'
#        prob = db.problems.find_one({'pid': prob})
#    generator = imp.load_source(prob['generator'][:-3], 'autogenerators/'+prob['generator'])
#    if hasattr(generator, 'validate_dependencies') and callable(generator.validate_dependencies):
#        if not generator.validate_dependencies():
#            return None
#    if hasattr(generator, 'generate') and callable(generator.generate):
#        auto_generators[prob['pid']] = generator
#        return generator
#    return None
#
#
#def move_temporary_files(file_list, desc):
#    """Move files in the tmp directory.
#
#    Takes a list of temporary files and a problem description. The files are enumerated and moved to the web
#    auto-problems directory (publicly accessible) and performs a string substitution on the passed problem desc
#    replacing the enumerated strings in the form ###file_X_url### with publicly accessible file path.
#    """
#    for idx, file_path in enumerate(file_list):
#        file_name = basename(file_path)
#        write_path = _full_auto_prob_path() + file_name
#        print "Moving file %s to %s." % (file_path, write_path)
#        os.rename(file_path, _full_auto_prob_path() + file_name)
#        desc = desc.replace("###file_%s_url###" % str(idx + 1), "autoproblems/" + file_name)
#        os.chmod(write_path, S_IWUSR | S_IRUSR | S_IRGRP | S_IROTH)
#    return desc
#
#
#def build_problem_instance(prob, tid):
#    """Builds unique problem dependencies for an auto-generated problem.
#
#    Gets the auto-generator instance for the passed problem and generates a problem instance. If no generator is found
#    in the preloaded generator dict the generator script is loaded from the database. We then build the problem
#    dependencies, grader, and description using the generator module. We move temporary files generated by the
#    generator to the web path and perform description substitutions to enable external access to these resources.
#    We then update the team document to specify that an auto-generated problem has been created for this team.
#    """
#    generator = auto_generators.get(prob['pid'], None)
#    if generator is None:
#        print "Autogenerator for %s was not found in the precached list, rebuilding..." % prob['pid']
#        generator = load_autogenerator(prob['pid'])
#        if generator is None:
#            print "ERROR - load_autogenerator(pid) returned None for pid: " + prob['pid']
#    (file_list, grader, desc) = generator.generate()
#    if file_list is not None:
#        desc = move_temporary_files(file_list, desc)
#    if prob['grader'] == "key":
#        db.teams.update({'tid': tid}, {'$set': {'probinstance.'+prob['pid']: {'pid': prob['pid'],
#                                                                              'desc': desc,
#                                                                              'key': grader}}})
#    elif prob['grader'] == 'file':
#        db.teams.update({'tid': tid}, {'$set': {'probinstance.'+prob['pid']: {'pid': prob['pid'],
#                                                                              'desc': desc,
#                                                                              'grader': grader}}})
#    return desc


def load_problems():
    """Gets the list of all problems.

    First check for 'problems' in the cache, if it exists return it otherwise rebuild the unlocked list.
    Query all problems from the database as well as all submissions from the current team.
    Cycle over all problems while looking at their weightmap, check to see if problems in the weightmap are solved.
    Increment the threshold counter for solved weightmap problems.
    If the threshold counter is higher than the problem threshold then add the problem to the return list (ret).
    """
    problems = cache.get('problems')
    if problems is None:
        problems = list(db.problems.find(
            {
                "enabled": {"$ne": False}
            },
            {
                "_id": 0, 
                "pid": 1, 
                "category": 1, 
                "displayname": 1, 
                "hint": 1,
                "basescore": 1, 
                "desc": 1
            }))

        """
        problems = []
        for p in list(db.problems.find()):
            #if 'weightmap' not in p or 'threshold' not in p or sum([p['weightmap'][pid] for pid in correctPIDs if pid in p['weightmap']]) >= p['threshold']:
            if 'enabled' not in p or p['enabled']:
                problems.append({'pid':            p['pid'],
                                 'category':       p.get('category', None),
                                 'displayname':    p.get('displayname', None),
                                 'hint':           p.get('hint', None),
                                 'basescore':      p.get('basescore', None),
                                 #'correct':        True if p['pid'] in correctPIDs else False,
                                 'desc':           p.get('desc') })
        """
        problems.sort(key=lambda k: (k['basescore'] if 'basescore' in k else 99999, k['pid']))
        cache.set('problems', json.dumps(problems), 60 * 60)
    else:
        problems = json.loads(problems)
    return problems


def load_problems_tid(tid):
    """Gets the list of all problems, with the solved/unsolved info of tid.

    First check for 'problems' in the cache, if it exists return it otherwise rebuild the unlocked list.
    Query all problems from the database as well as all submissions from the current team.
    Cycle over all problems while looking at their weightmap, check to see if problems in the weightmap are solved.
    Increment the threshold counter for solved weightmap problems.
    If the threshold counter is higher than the problem threshold then add the problem to the return list (ret).
    """
    problems_tid = cache.get('problems_' + tid)
    if problems_tid is None:
        solved = get_solved_problems(tid)
        problems_tid = load_problems()
        for p in problems_tid:
            p['correct'] = p['pid'] in solved
        cache.set('problems_' + tid, json.dumps(problems_tid), 60 * 60)
    else:
        problems_tid = json.loads(problems_tid)

    return problems_tid


#def load_unlocked_problems(tid):
#    """Gets the list of all unlocked problems for a team.
#
#    First check for 'unlocked_<tid>' in the cache, if it exists return it otherwise rebuild the unlocked list.
#    Query all problems from the database as well as all submissions from the current team.
#    Cycle over all problems while looking at their weightmap, check to see if problems in the weightmap are solved.
#    Increment the threshold counter for solved weightmap problems.
#    If the threshold counter is higher than the problem threshold then add the problem to the return list (ret).
#    """
#    unlocked = cache.get('unlocked_' + tid)  # Get the teams list of unlocked problems from the cache
#    if unlocked is not None:  # Return this if it is not empty in the cache
#        return json.loads(unlocked)
#    unlocked = []
#    team = db.teams.find_one({'tid': tid})
#    if 'probinstance' not in team.keys():
#        db.teams.update({'tid': tid}, {'$set': {'probinstance': {}}})
#        team['probinstance'] = dict()
#    correctPIDs = {p['pid'] for p in list(db.submissions.find({"tid": tid, "correct": True}))}
#    for p in list(db.problems.find()):
#        if 'weightmap' not in p or 'threshold' not in p or sum([p['weightmap'][pid] for pid in correctPIDs if pid in p['weightmap']]) >= p['threshold']:
#            unlocked.append({'pid':            p['pid'],
#                             'category':       p.get('category', None),
#                             'displayname':    p.get('displayname', None),
#                             'hint':           p.get('hint', None),
#                             'basescore':      p.get('basescore', None),
#                             'correct':        True if p['pid'] in correctPIDs else False,
#                             'desc':           p.get('desc') if not p.get('autogen', False)
#                             else team['probinstance'][p['pid']].get('desc', None) if p['pid'] in team.get('probinstance', dict())
#                             else build_problem_instance(p, tid)})
#
#    unlocked.sort(key=lambda k: k['basescore'] if 'basescore' in k else 99999)
#    cache.set('unlocked_' + tid, json.dumps(unlocked), 60 * 60)
#    return unlocked


def get_solved_problems(tid):
    """Returns a list of all problems the team has solved.

    Checks for 'solved_<tid>' in the cache, if the list does not exists it rebuilds/inserts it.
    Queries the database for all submissions by the logged in team where correct == True.
    Finds all problems with a PID in the list of correct submissions.
    All solved problems are returned as a pid and display name.
    """

    solved = cache.get('solved_' + tid)
    if solved is None:
        solved = list((p['pid'] for p in db.submissions.find({"tid": tid, "correct": True}, {"pid": 1})))
        cache.set('solved_' + tid, json.dumps(solved), 60 * 60)
    else:
        solved = json.loads(solved)
    return solved


#def get_single_problem(pid, tid):
#    """Retrieve a single problem.
#
#    Grab all problems from load_unlocked_problems (most likely cached). Iterate over the problems looking for the
#    desired pid. Return the problem if found. If not found return status:0 with an error message.
#    """
#    for prob in load_unlocked_problems(tid):
#        if prob['pid'] == pid:
#            return prob
#    return {'status': 0, 'message': 'Internal error, problem not found.'}


def submit_problem(tid, request, is_zju_user):
    """Handle problem submission.

    Gets the key and pid from the submitted problem, calls the respective grading function if the values aren't empty.
    If correct all relevant cache values are cleared. The submission is the inserted into the database
    (an attempt is made). A relevant message is returned if the problem has already been solved or the answer
    has been tried.
    """

    """
    response = captcha.submit(
        request.form.get('recaptcha_challenge', ''),
        request.form.get('recaptcha_response', ''),
        '6LcPFPESAAAAAIkncbbAOfUi6sTSrMMxKVA9EcMq',
        request.remote_addr
    )

    if not response.is_valid:
        return {"status": 0, "points": 0, "message": "验证码不正确."}
    """

    t_interval = 10
    last_submitted = cache.get('last_submitted_' + tid)
    if not last_submitted:
        cache.set('last_submitted_' + tid, True, t_inverval)
    else:
        return {"status": 0, "points": 0, "message": "相邻提交之间隔须多于%d秒, 请稍后再试." % t_interval}

    pid = request.form.get('pid', '')
    key = request.form.get('key', '')
    if pid == '':
        return {"status": 0, "points": 0, "message": "题目名字不能为空."}
    if key == '':
        return {"status": 0, "points": 0, "message": "答案不能为空."}
    #if pid not in [p['pid'] for p in load_unlocked_problems(tid)]:
    #    return {"status": 0, "points": 0, "message": "You cannot submit problems you have not unlocked."}
    pid = pid.encode('utf8').strip()
    # key = key.encode('utf8').strip()
    prob = cache.get('problem_' + pid)
    if prob is None:
        prob = db.problems.find_one({"pid": pid})
        if prob is None:
            return {"status": 0, "points": 0, "message": "未找到题目'%s'." %pid}
        del prob['_id']
        cache.set('problem_' + pid, json.dumps(prob), 60 * 60)
    else:
        prob = json.loads(prob)

    correct = False
    grader_type = prob.get('grader-type', 'key')
    if grader_type == 'file':
        (correct, message) = imp.load_source(prob['grader'][:-3], "./graders/" + prob['grader']).grade(tid, key)
    elif grader_type == 'key':
        correct = prob['key'] == key
        message = prob.get('correct_msg', '回答正确!') if correct else prob.get('wrong_msg', '回答错误!')

    submission = {'tid': tid,
                  'timestamp': utilities.timestamp(datetime.utcnow()),
                  'pid': pid,
                  'ip': request.headers.get('X-Real-IP', None),
                  'key': key,
                  'correct': correct}
    if correct:
        #cache.delete('unlocked_' + tid)  # Clear the unlocked problem cache as it needs updating
        cache.delete('solved_' + tid)  # Clear the list of solved problems
        cache.delete('problems_' + tid)
        if is_zju_user:
            cache.delete('scoreboard_zju')  
        else:
            cache.delete('scoreboard_public')  
        cache.delete('teamscore_' + tid)  # Clear the team's cached score
        cache.delete('lastsubdate_' + tid)
        try:
            db.submissions.insert(submission)
        except DuplicateKeyError:
            return {"status": 0, "points": 0, "message": "你已解决此题!"}
    else:
        try:
            db.submissions.insert(submission)
        except DuplicateKeyError:
            return {"status": 0, "points": 0, "message": "你已提交过这一错误答案!"}
    return {"status": 1 if correct else 0, "points": prob.get('basescore', 0), "message": message}


def _full_auto_prob_path():
    return root_web_path + relative_auto_prob_path
