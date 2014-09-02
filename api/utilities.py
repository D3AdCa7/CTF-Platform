# 
# -*- coding: utf-8 -*-

__author__ = "Collin Petty"
__copyright__ = "Carnegie Mellon University"
__license__ = "MIT"
__maintainer__ = ["Collin Petty", "Peter Chapman"]
__credits__ = ["David Brumely", "Collin Petty", "Peter Chapman", "Tyler Nighswander", "Garrett Barboza"]
__email__ = ["collin@cmu.edu", "peter@cmu.edu"]
__status__ = "Production"


import smtplib
from common import db
from common import cache
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
import bcrypt
import common
import json
import datetime
import time
import calendar
import re

enable_email = False

smtp_url = ''
email_username = ''
email_password = ''
from_addr = ''
from_name = ''

site_domain = ''


def timestamp(dt):
    return calendar.timegm(dt.timetuple())


def is_zju_email(email):
    zju_email = [
        '@zju.edu.cn',
        '@st.zju.edu.cn',
        '@gstu.zju.edu.cn',
        '@fa.zju.edu.cn',
    ]
    return email.endswith('zju.edu.cn')
    #return any([email.endswith(suffix) for suffix in zju_email])


def send_email(recip, subject, body):
    """Send an email with the given body text and subject to the given recipient.

    Generates a MIMEMultipart message, connects to an smtp server using the credentials loaded from the configuration
    file, then sends the email.
    """
    if enable_email:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = formataddr((from_name, from_addr))
        msg['To'] = recip
        part1 = MIMEText(body, 'plain')
        msg.attach(part1)
        s = smtplib.SMTP_SSL(smtp_url)
        s.login(email_username, email_password)
        s.sendmail(from_addr, recip, msg.as_string())
        s.quit()
    else:
        print "Emailing is disabled, not sending."


def send_email_to_list(recips, subject, body):
    """Sends an email to a list of recipients.

    If a list of recipients is passed we iterate over them and call send_email for each recipient."""
    if recips is not None:
        for recip in recips:
            print "Sending email to %s" % recip
            send_email(recip, subject, body)


def verify_email(request, session):
    """Performs the email address verification.

    Gets a token from the url parameters, if the token is found in a team object in the database
    the new password is hashed and set, the token is then removed and an appropriate response is returned.
    """
    token = request.args.get('token', None)
    if token is None or token == '':
        return {"status": 0, "message": "验证信息不能为空."}
    token = token.encode('utf8')

    team = db.teams.find_one({'emailverifytoken': token})
    if team is None:
        return {"status": 0, "message": "验证信息无效."}
    try:
        db.teams.update({'tid': team['tid']}, {'$set': {'email_verified': True}})
        db.teams.update({'tid': team['tid']}, {'$unset': {'emailverifytoken': 1}})
    except:
        return {"status": 0, "message": "验证邮箱失败. 请联系管理员."}
    if is_zju_email(team['email']):
        cache.delete('verified_teams_zju')
    else:
        cache.delete('verified_teams_public')
    session['tid'] = team['tid']
    session['teamname'] = team['teamname']
    session['is_zju_user'] = is_zju_email(team['email'])
    return {"status": 1, "message": "邮箱已被验证成功."}


def prepare_verify_email(team_name, team_email):
    """Prepares for verifying the email address with the team name.
    
    Generates a secure token and inserts it into the team's document as 'emailverifytoken'.
    A link is emailed to the registered email address with the random token in the url.  The user can go to this
    link to verify the email address.
    """
    team = db.teams.find_one({'teamname': team_name})
    assert(team != None)
    token = common.sec_token()
    db.teams.update({'tid': team['tid']}, {'$set': {'emailverifytoken': token}})

    msg_body = """
    We recently received a request of registration for the following 'ACTF' account:\n\n  - %s\n\n
    Our records show that this is the email address used to register the above account.  If you did not request to register with the above account then you need not take any further steps.  If you did request the registration please follow the link below to verify your email address. \n\n http://%s/api/verify?token=%s \n\n Best of luck! \n\n ~The 'ACTF' Team
    """ % (team_name, site_domain, token)

    send_email(team_email, "'ACTF' Email Verify", msg_body)
    return


def reset_password(request):
    """Perform the password update operation.

    Gets a token and new password from a submitted form, if the token is found in a team object in the database
    the new password is hashed and set, the token is then removed and an appropriate response is returned.
    """
    token = request.form.get('token', None)
    newpw = request.form.get('newpw', None)
    if token is None or token == '':
        return {"status": 0, "message": "密码重设密钥不能为空."}
    if newpw is None or newpw == '':
        return {"status": 0, "message": "新密码不能为空."}
    token = token.encode('utf8')
    newpw = newpw.encode('utf8')

    team = db.teams.find_one({'passrestoken': token})
    if team is None:
        return {"status": 0, "message": "密码重设密钥无效."}
    try:
        db.teams.update({'tid': team['tid']}, {'$set': {'pwhash': bcrypt.hashpw(newpw, bcrypt.gensalt(8))}})
        db.teams.update({'tid': team['tid']}, {'$unset': {'passrestoken': 1}})
        db.teams.update({'tid': team['tid']}, {'$set': {'email_verified': True}})
    except:
        return {"status": 0, "message": "重设密码出现错误. 请重试或联系管理员."}
    if not team['email_verified']:
        if is_zju_email(team['email']):
            cache.delete('verified_teams_zju')
        else:
            cache.delete('verified_teams_public')
    return {"status": 1, "message": "密码已被重设."}


def request_password_reset(request):
    """Emails a user a link to reset their password.

    Checks that a teamname was submitted to the function and grabs the relevant team info from the db.
    Generates a secure token and inserts it into the team's document as 'passresttoken'.
    A link is emailed to the registered email address with the random token in the url.  The user can go to this
    link to submit a new password, if the token submitted with the new password matches the db token the password
    is hashed and updated in the db.
    """
    teamname = request.form.get('teamname', None)
    if teamname is None or teamname == '':
        return {"success": 0, "message": "用户名不能为空."}
    teamname = teamname.encode('utf8').strip()
    team = db.teams.find_one({'teamname': teamname})
    if team is None:
        return {"success": 0, "message": "未找到用户'%s'." % teamname}
    teamEmail = team['email']
    token = common.sec_token()
    db.teams.update({'tid': team['tid']}, {'$set': {'passrestoken': token}})

    msgBody = """
    We recently received a request to reset the password for the following 'ACTF' account:\n\n  - %s\n\n
    Our records show that this is the email address used to register the above account.  If you did not request to reset the password for the above account then you need not take any further steps.  If you did request the password reset please follow the link below to set your new password. \n\n http://%s/passreset#%s \n\n Best of luck! \n\n ~The 'ACTF' Team
    """ % (teamname, site_domain, token)

    send_email(teamEmail, "'ACTF' Password Reset", msgBody)
    return {"success": 1, "message": "密码重设邮件已被发送. 请注意查收."}


def lookup_team_names(email):
    """Get all team names associated with an email address.

    Queries db for all teams with email equal to the provided email address, sends the names of all the team names
    to the email address.
    """
    if email == '':
        return {"status": 0, "message": "Email Address cannot be empty."}
    teams = list(db.teams.find({'email': {'$regex': email, '$options': '-i'}}))
    if len(teams) == 0:
        return {"status": 0, "message": "No teams found with that email address, please register!"}
    tnames = [t['teamname'] for t in teams]
    msgBody = """Hello!

    We recently received a request to lookup the team names associated with your email address.  If you did not request this information then please disregard this email.

    The following teamnames are associated with your email address (%s).\n\n""" % email
    for tname in tnames:
        msgBody += "\t- " + tname + "\n"

    msgBody += """\nIf you have any other questions, feel free to contact us at other@example.com

    Best of luck!

    ~The 'CTF Platform' team
    """
    send_email(email, "'CTF Platform' Teamname Lookup", msgBody)
    return {"status": 1, "message": "An email has been sent with your registered teamnames."}


#def get_verified_teams():
#    """Get list of email-verified teams
#
#    Do a cached query.
#    """
#    verified_teams = cache.get('verified_teams')
#    if verified_teams is None:
#        verified_teams = list(db.teams.find({"email_verified": True}, {"_id": 0, "teamname": 1, "tid": 1}))
#        cache.set('verified_teams', json.dumps(verified_teams), 60 * 60)
#    else:
#        verified_teams = json.loads(verified_teams)
#
#    return verified_teams


def get_verified_teams_public():
    """Get list of email-verified teams public

    Do a cached query.
    """
    verified_teams = cache.get('verified_teams_public')
    if verified_teams is None:
        verified_teams = list(db.teams.find({
            "email_verified": True,
            "email": {"$not": re.compile(".*zju\.edu\.cn$")}
        }, {
            "_id": 0, 
            "teamname": 1, 
            "tid": 1
        }))
        cache.set('verified_teams_public', json.dumps(verified_teams), 60 * 60)
    else:
        verified_teams = json.loads(verified_teams)
    return verified_teams


def get_verified_teams_zju():
    """Get list of email-verified teams zju

    Do a cached query.
    """
    verified_teams = cache.get('verified_teams_zju')
    if verified_teams is None:
        verified_teams = list(db.teams.find({
            "email_verified": True,
            "email": {"$regex": r".*zju\.edu\.cn$"}
        }, {
            "_id": 0, 
            "teamname": 1, 
            "tid": 1
        }))
        cache.set('verified_teams_zju', json.dumps(verified_teams), 60 * 60)
    else:
        verified_teams = json.loads(verified_teams)

    return verified_teams


def load_news():
    """Get news to populate the news page.

    Queries the database for all news articles, loads them into a json document and returns them ordered by their date.
    Newest articles are at the beginning of the list to appear at the top of the news page.
    """
    news = cache.get('news')
    if news is not None:
        return json.loads(news)
    news = sorted([{'date': n['date'] if 'date' in n else "2000-01-01",
                    'header': n['header'] if 'header' in n else None,
                    'articlehtml': n['articlehtml' if 'articlehtml' in n else None]}
                   for n in list(db.news.find())], key=lambda k: k['date'], reverse=True)
    cache.set('news', json.dumps(news), 60 * 2)
    return news
