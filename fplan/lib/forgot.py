
# Import smtplib for the actual sending function
import smtplib

# Import the email modules we'll need
from email.mime.text import MIMEText
import os
from fplan.lib.helpers import md5str
import base64
import routes.util as h
from fplan.model import meta,User,Trip,Waypoint,Route
import sqlalchemy as sa


def decode_challenge(challenge):
    d=base64.b16decode(challenge)
    dhash=d[0:32]
    username=unicode(d[32:],'utf-8')

    users=meta.Session.query(User).filter(sa.and_(
            User.user==username)
            ).all()
    if len(users)==0: return None
    user,=users
    
    buf=(user.lastlogin.strftime("%Y-%m-%d")+user.user+user.password).encode('utf-8')
    hash=md5str(buf)
    assert len(hash)==32
    challenge=hash+user.user.encode('utf-8')
    print "Challenge: %s, Should be: %s"%(d,challenge)
    if challenge==d:
        return user
    return None
    

def forgot_password(user):
    if not user.user.count("@"):
        return False
    
    buf=(user.lastlogin.strftime("%Y-%m-%d")+user.user+user.password).encode('utf-8')
    hash=md5str(buf)
    assert len(hash)==32
    challenge=hash+user.user.encode('utf-8')
        
    link=h.url_for(controller='splash',action="reset",code=base64.b16encode(challenge))
    msgbody="""
Hello!
    
This is an automated message from the %(site)s website, generated because someone has clicked the "forgot password" button on the login page.
    
If you did not do so, you may safely ignore this message. Otherwise, please follow this link to reset your password:
    
http://%(site)s%(link)s
  
If you feel that you should not have received this message, and think that someone should know, you may contact anders.musikka@gmail.com
"""%dict(site=os.getenv('SWFP_HOSTNAME','example.com'),link=link)
    
    msg = MIMEText(msgbody)
        
    # me == the sender's email address
    # you == the recipient's email address
    from_='forgot@%s'%(os.getenv('SWFP_HOSTNAME','example.com'),)
    msg['Subject'] = 'Reset Password'
    msg['From'] = from_
    msg['To'] = user.user
    
    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    s = smtplib.SMTP('localhost')
    print "Sending mail with body: %s"%(msg,)
    s.sendmail(from_, user.user, msg.as_string())
    s.quit()
    return True
