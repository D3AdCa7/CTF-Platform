#
# -*- coding: utf-8 -*-

__author__ = ["Collin Petty", "Peter Chapman"]
__copyright__ = "Carnegie Mellon University"
__license__ = "MIT"
__maintainer__ = ["Collin Petty", "Peter Chapman"]
__credits__ = ["David Brumely", "Collin Petty", "Peter Chapman", "Tyler Nighswander", "Garrett Barboza"]
__email__ = ["collin@cmu.edu", "peter@cmu.edu"]
__status__ = "Production"


import bcrypt
from common import db
debug_disable_general_login = False

import utilities


def login(request, session):
    """Authenticates a user.

    Takes POSTed auth credentials (teamname and password) and validates to mongo, adds the teamID to the session dict.
    If the debug_disable_general_login flag is set only accounts with 'debugaccount' set to true will be able
    to authenticate.
    """

    if 'tid' in session:  # we assume that if there is a tid in the session dict then the user is authenticated
        return {"success": 1, "message": "你已经登录了."}
    teamname = request.form.get('teamname', None)  # get the teamname and password from the POSTed form
    password = request.form.get('password', None)
    if teamname is None or teamname == '':
        return {'success': 0, 'message': "用户名不能为空."}
    if password is None or password == '':  # No password submitted
        return {"success": 0, "message": "密码不能为空."}
    if len(teamname) > 250:
        return {"success": 0, "message": "STAHP!"}
    teamname = teamname.encode('utf8').strip()
    password = password.encode('utf8')
    teamCurr = db.teams.find({'teamname': teamname})
    if teamCurr.count() == 0:  # No results returned from mongo when searching for the user
        return {"success": 0, "message": "未找到用户名'%s'." % teamname}
    if teamCurr.count() > 1:
        return {"success": 0, "message": "查找用户信息失败. 请联系管理员."}
    checkTeam = teamCurr[0]
    if checkTeam['email_verified'] == False:
        return {"success": 0, "message": "请先访问邮箱查收验证邮件."}
    pwhash = checkTeam['pwhash']  # The pw hash from the db
    if bcrypt.hashpw(password, pwhash) == pwhash:
        if checkTeam.get('debugaccount', None):
            session['debugaccount'] = True
        if debug_disable_general_login:
            if 'debugaccount' not in checkTeam or not checkTeam['debugaccount']:
                return {'success': 2, "message": "Correct credentials! But the game has not started yet..."}
        if checkTeam['tid'] is not None:
            session['tid'] = checkTeam['tid']
            session['teamname'] = checkTeam['teamname']
            session['is_zju_user'] = utilities.is_zju_email(checkTeam['email'])
        else:  # SET THE 'tid' TO str('_id') FOR MIGRATION PURPOSES AND ADD THE 'tid' TO THE DOCUMENT
            session['tid'] = checkTeam['_id']
            session['teamname'] = checkTeam['teamname']
            session['is_zju_user'] = utilities.is_zju_email(checkTeam['email'])
            db.teams.update({'_id': checkTeam['_id']}, {'tid': checkTeam['_id']})
        return {"success": 1, "message": "用户'%s'登录成功." % teamname,
            'teamname': session['teamname'], 'is_zju_user': session['is_zju_user']}
    return {"success": 0, "message": "密码错误."}


def logout(session):
    """Logout

    If the user has a teamID in the session it is removed and success:1 is returned.
    If teamID is not in session success:0 is returned.
    """

    if 'tid' in session:
        session.clear()
        return {"success": 1, "message": "注销成功."}
    else:
        return {"success": 0, "message": "你之前并未处于登录状态."}


def is_logged_in(session):
    """Check if the user is currently logged in.

    If the user has a teamID in their session return success:1 and a message
    If they are not logged in return a message saying so and success:0
    """
    if 'tid' in session:
        return {'success': 1, 'message': '你处于登录状态.', 
            'teamname': session['teamname'], 'is_zju_user': session['is_zju_user']}
    else:
        return {"success": 0, "message": "你并未处于登录状态."}


def is_blacklisted(tid):
    return db.teams.find_one({'tid': tid}).get('blacklisted', False)
