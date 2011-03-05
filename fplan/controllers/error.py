import cgi

from paste.urlparser import PkgResourcesParser
from pylons import request
from pylons.controllers.util import forward
from pylons.middleware import error_document_template
from webhelpers.html.builder import literal

from fplan.lib.base import BaseController,render

class ErrorController(BaseController):

    """Generates error documents as and when they are required.

    The ErrorDocuments middleware forwards to ErrorController when error
    related status codes are returned from the application.

    This behaviour can be altered by changing the parameters to the
    ErrorDocuments middleware in your config/middleware.py file.

    """
    def document(self):
        """Render the error document"""
        resp = request.environ.get('pylons.original_response')
        if hasattr(resp,'status_int') and resp.status_int:
            code=repr(resp.status_int)
        else:
            code=repr(request.GET.get('code', ''))
            
        msg=request.GET.get('message', '')
        if msg and not code:
            what=msg
        elif not msg and code:
            what="code: %s"%(code,)
        else:
            what=":".join(x for x in [code,msg] if x)
        return render('/error.mako',extra_vars=dict(what=what))

    def img(self, id):
        """Serve Pylons' stock images"""
        return self._serve_file('/'.join(['media/img', id]))

    def style(self, id):
        """Serve Pylons' stock stylesheets"""
        return self._serve_file('/'.join(['media/style', id]))

    def _serve_file(self, path):
        """Call Paste's FileApp (a WSGI application) to serve the file
        at the specified path
        """
        request.environ['PATH_INFO'] = '/%s' % path
        return forward(PkgResourcesParser('pylons', 'pylons'))
