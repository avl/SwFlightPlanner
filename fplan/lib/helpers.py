"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to templates as 'h'.
"""
# Import helpers as desired, or define your own, ie:
#from webhelpers.html.tags import checkbox, password
from routes.util import url_for
from itertools import count,izip
import cgi
from pylons import request, response, session, tmpl_context as c


def get_username():
    if session.get('isreg',False):
        return "Logged in as %s&nbsp;&nbsp;"%(cgi.escape(session['user']),)
    return "Anonymous <a href=\"%s\">Create User</a>"%(url_for(controller="profile",action="index"),)

