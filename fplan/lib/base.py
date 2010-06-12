"""The base Controller API

Provides the BaseController class for subclassing.
"""
from pylons.controllers import WSGIController
from pylons.templating import render_mako as render
from pylons import request, response, session
from pylons.controllers.util import abort, redirect_to
import routes.util as h 
from fplan.model import meta,User

class BaseController(WSGIController):
    def __before__(self):    
        if hasattr(self,"no_login_required") and self.no_login_required==True:
            return
        # Authentication required?
        
        #print "User:",session.get('user',None)
        users=meta.Session.query(User).filter(
                User.user==session['user']).all()
        if (not ('user' in session)) or len(users)==0:
            #create a default user which may subsequently be renamed if user wishes to
            base=""
            for seed in open("/dev/urandom").read(8):
                base+=chr(ord('A')+ord(seed)%16)
                base+=chr(ord('A')+ord(seed)/16)
            for i in xrange(1000):
                cand=base+str(i)                            
                if meta.Session.query(User).filter(
                    User.user==cand).count()==0:
                    user1 = User(cand, "")
                    meta.Session.add(user1)                    
                    meta.Session.flush()
                    meta.Session.commit()
                    print "Users:",meta.Session.query(User).all()
                    session['user']=cand
                    session['realuser']=False
                    session.save()
                    return
            raise Exception("Couldn't generate temporary user name")
        if len(users)==1:
            if session.get('isreg',False)!=users[0].isregistered:
                session['isreg']=users[0].isregistered
    def __call__(self, environ, start_response):
        """Invoke the Controller"""
        # WSGIController.__call__ dispatches to the Controller method
        # the request is routed to. This routing information is
        # available in environ['pylons.routes_dict']
        try:
            return WSGIController.__call__(self, environ, start_response)
        finally:
            meta.Session.remove()
