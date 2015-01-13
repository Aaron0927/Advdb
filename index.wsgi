import pylibmc
import sys
sys.modules['memcache'] = pylibmc
import sae
from advdbSite import wsgi
application = sae.create_wsgi_app(wsgi.application)