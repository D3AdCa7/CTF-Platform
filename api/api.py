#
# -*- coding: utf-8 -*-

__author__ = ["Collin Petty", "Peter Chapman"]
__copyright__ = "Carnegie Mellon University"
__license__ = "MIT"
__maintainer__ = ["Collin Petty", "Peter Chapman"]
__credits__ = ["David Brumely", "Collin Petty", "Peter Chapman", "Tyler Nighswander", "Garrett Barboza"]
__email__ = ["collin@cmu.edu", "peter@cmu.edu"]
__status__ = "Production"


import logging
from flask import Flask, request, session, abort, redirect
from functools import wraps
import json
import random
from datetime import datetime

import account
import auth
import common
import group
import problem
import scoreboard
import utilities
import ConfigParser

app = Flask("ctf")


def require_login(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        if 'tid' not in session:
            abort(403)
        return f(*args, **kwds)
    return wrapper


def deny_blacklisted(f):
    @wraps(f)
    @require_login
    def wrapper(*args, **kwds):
        if auth.is_blacklisted(session['tid']):
            abort(403)
        return f(*args, **kwds)
    return wrapper


def return_json(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        return json.dumps(f(*args, **kwds), encoding='utf8', 
            separators=(',', ':'))
    return wrapper


@app.before_first_request
def setup_logging():
    if not app.debug:
        app.logger.addHandler(logging.StreamHandler())
        app.logger.setLevel(logging.INFO)


@app.route('/api/login', methods=['POST'])
@return_json
def login_hook():
    session['_rd'] = random.getrandbits(32)
    return auth.login(request, session)


@app.route('/api/logout', methods=['GET'])
@return_json
def logout_hook():
    return auth.logout(session)


@app.route('/api/isloggedin', methods=['GET'])
@return_json
def is_logged_in_hook():
    return auth.is_logged_in(session)


@app.route('/api/register', methods=['POST'])
@return_json
def register_team_hook():
    return account.register_team(request)


@app.route('/api/updatepass', methods=['POST'])
@return_json
@require_login
def update_password_hook():
    return account.update_password(session['tid'], request)


@app.route('/api/problems', methods=['GET'])
@require_login
@return_json
def load_problems_hook():
    return problem.load_problems_tid(session['tid'])


"""
@app.route('/api/problems/solved', methods=['GET'])
@require_login
@return_json
def get_solved_problems_hook():
    return problem.get_solved_problems(session['tid'])


@app.route('/api/problems/<path:pid>', methods=['GET'])
@require_login
@return_json
def get_single_problem_hook(pid):
    problem_info = problem.get_single_problem(pid, session['tid'])
    if 'status' not in problem_info:
        problem_info.update({"status": 1})
    return problem_info
"""


@app.route('/api/requestpasswordreset', methods=['POST'])
@return_json
def request_password_reset_hook():
    return utilities.request_password_reset(request)


@app.route('/api/resetpassword', methods=['POST'])
@return_json
def reset_password_hook():
    return utilities.reset_password(request)


@app.route('/api/verify', methods=['GET'])
def verify_hook():
    ret = utilities.verify_email(request, session)
    if ret['status'] == 1:
        return redirect('http://%s/account' %utilities.site_domain)
    return json.dumps(ret)


"""
@app.route('/api/lookupteamname', methods=['POST'])
@return_json
def lookup_team_names_hook():
    return utilities.lookup_team_names(request.form.get('email', '').encode('utf8'))


@app.route('/api/creategroup', methods=['POST'])
@require_login
@return_json
def create_group_hook():
    return group.create_group(session['tid'], request.form.get('name', '').encode('utf8'))


@app.route('/api/joingroup', methods=['POST'])
@require_login
@return_json
def join_group_hook():
    gname = request.form.get('name', '').encode('utf8')
    return group.join_group(session['tid'], gname)


@app.route('/api/groups', methods=['GET'])
@require_login
@return_json
def get_group_membership_hook():
    return group.get_group_membership(session['tid'])


@app.route('/api/leavegroup', methods=['POST'])
@require_login
@return_json
def leave_group_hook():
    gid = request.form.get('gid', '').encode('utf8')
    return group.leave_group(session['tid'], gid)


@app.route('/api/score', methods=['GET'])
@require_login
@return_json
def load_team_score_hook():
    return {'score': scoreboard.load_team_score(session['tid'])}
"""


@app.route('/api/scoreboards', methods=['GET'])
@return_json
def get_scoreboards_hook():
    return scoreboard.get_scoreboard(session)


@app.route('/api/submit', methods=['POST'])
@return_json
@require_login
def submit_problem_hook():
    ret = problem.submit_problem(session['tid'], request, session['is_zju_user'])
    tstamp = utilities.timestamp(datetime.utcnow())
    if tstamp > scoreboard.ctf_end:
        ret['message'] = '[比赛已经结束] %s' % ret['message']
        ret['status'] = 0
        ret['sore'] = 0
    return ret


@app.route('/api/news', methods=['GET'])
@return_json
def load_news_hook():
    return utilities.load_news()


"""
@app.route('/api/getsshacct', methods=['GET'])
@return_json
@require_login
def get_ssh_account_hook():
    return account.get_ssh_account(session['tid'])
"""


@app.after_request
def after_request(response):
    if (request.headers.get('Origin', '') in
            ['http://example.com',
             'http://www.example.com']):
        response.headers.add('Access-Control-Allow-Origin',
                             request.headers['Origin'])
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, *')
    response.headers.add('Cache-Control', 'no-cache')
    response.headers.add('Cache-Control', 'no-store')
    response.mimetype = 'application/json'
    return response


def initialize():
    common.log_level = ['ERROR', 'INFO']
    config = ConfigParser.ConfigParser()
    config.read('mister.config')
    if config.get('debug', 'admin_emails') is not None:
        common.admin_emails = list()
    for email in config.get('debug', 'admin_emails').split(','):
        common.admin_emails.append(email.strip())

    app.config['DEBUG'] = False
    secret_key = config.get('flask', 'secret_key').decode('hex')
    if secret_key == '':
        common.log('The Flask secret key specified in the config file is empty.')
        exit()
    app.secret_key = secret_key
    app.config['SESSION_COOKIE_HTTPONLY'] = False
    app.config['SESSION_COOKIE_DOMAIN'] = config.get('flask', 'SESSION_COOKIE_DOMAIN')
    app.config['SESSION_COOKIE_PATH'] = config.get('flask', 'SESSION_COOKIE_PATH')
    app.config['SESSION_COOKIE_NAME'] = config.get('flask', 'SESSION_COOKIE_NAME')
    app.config['PERMANENT_SESSION_LIFETIME'] = int(config.get('flask','PERMANENT_SESSION_LIFETIME'))

    enable_email = config.get('email', 'enable_email')
    if enable_email:
        common.log('Enabling Email support.', 'INFO')
        utilities.enable_email = enable_email
    smtp_url = config.get('email', 'smtp_url')
    common.log("SMTP Server set to '%s'" % smtp_url, 'INFO')
    utilities.smtp_url = smtp_url

    email_username = config.get('email', 'username')
    common.log("SMTP username set to '%s'" % email_username, 'INFO')
    utilities.email_username = email_username

    email_password = config.get('email', 'password')
    common.log("SMTP password set to '%s'" % ('*' * len(email_password)), 'INFO')
    utilities.email_password = email_password

    from_addr = config.get('email', 'from_addr')
    common.log("Email from addr set to '%s'" % from_addr, 'INFO')
    utilities.from_addr = from_addr

    from_name = config.get('email', 'from_name')
    common.log("Setting sender name to '%s'" % from_name, 'INFO')
    utilities.from_name = from_name

    site_domain = config.get('misc', 'site_domain').encode('utf8')
    assert(site_domain)
    utilities.site_domain = site_domain

    problem.root_web_path = config.get('autogen', 'root_web_path')
    problem.relative_auto_prob_path = config.get('autogen', 'relative_auto_prob_path')
    common.log_level = ['ERROR']


initialize()  # load all config settings and configure flask keys
#problem.load_autogenerators()  # load all auto-generated problems

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, threaded=True, debug=False)
