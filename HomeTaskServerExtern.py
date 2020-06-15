import cherrypy
import datetime
from os import path

CHERRY_SERVER_EXP_CFG = path.join(path.dirname(__file__), "config", "cherry_expose_config.conf")
HOMEPAGE_EXP = path.join("generated_files","index_expose.php")

class ExposedFrontEnd:
    """ This is the server we expose to the WWW """
    
    @cherrypy.expose
    def index(self, cmd=None, task=None):
        """ home page """
        generate_frontend_external()
        return open(HOMEPAGE_EXP)

    @cherrypy.expose
    def temperatures(self):
        return open(path.join("generated_files","temperatures.html"))

    @cherrypy.expose
    def co2(self):
        return open(path.join("generated_files","co2.html"))

def secureheaders():
    headers = cherrypy.response.headers
    headers['X-Frame-Options'] = 'DENY'
    headers['X-XSS-Protection'] = '1; mode=block'
    headers['Content-Security-Policy'] = "default-src='self'"

def generate_frontend_external():
    """ Once the tasks are all loaded, create a home page with their data """
    now = datetime.datetime.utcnow()
    
    with open(HOMEPAGE_EXP,"w") as f:
        f.write('<!DOCTYPE html><html lang="en"><body>')
        f.write('UTC Time: %s <br><br>' % str(now))
        f.write('<br><br><a href="/">Reload</a> . . . . . . . <a href="temperatures">Temp Graph</a> . . . . .  . . . . . <a href="co2">CO2 Graph</a>')
        f.write('<br><br>')
        f.write('</body></html>')

def start_exposed_server():
    # Start our external server
    generate_frontend_external()

    cherrypy.tools.secureheaders = cherrypy.Tool('before_finalize', secureheaders, priority=60)
    cherrypy.quickstart(ExposedFrontEnd(), config=CHERRY_SERVER_EXP_CFG)

if __name__ == '__main__':
    print("Starting External Server")
    start_exposed_server()


