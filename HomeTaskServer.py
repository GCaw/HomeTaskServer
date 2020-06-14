import json
import cherrypy
import datetime
import sys
import threading
from os import path

from tasks.task_base import BaseTask
from tasks.task_onlineweather import OutsideTempTask
from tasks.task_localenvironment import IndoorTempPressTask, IndoorCO2
from tasks.task_expressentry import CandaInstructionTask
from tasks.task_nas import NasWake, NasCheckSmart, NasShutdown
from tasks.task_checkip import UpdateIP

CHERRY_SERVER_CFG = path.join("conf","cherry_config.conf")
CHERRY_SERVER_EXP_CFG = path.join("conf","cherry_expose_config.conf")

TASK_JSON_CFG = path.join("conf","task_config.json")
HOMEPAGE = path.join("generated_files","index.php")
HOMEPAGE_EXP = path.join("generated_files","index_expose.php")

tasks = []

class LocalFrontEnd:
    """
    This is our local server, there are many like it, but this is ours
    """
    @cherrypy.expose
    def index(self, cmd=None, task=None):
        """ home page, if there is get-info we do something before displaying """
        # process any commands
        if not (cmd == None):
            if (task==None):
                return "No task id provided"
            if (cmd=="pause"):
                tasks[int(task)].startstop_task()
            if (cmd=="runnow"):
                tasks[int(task)].trigger_run_now()
            
        generate_frontend_local(tasks)
        return open(HOMEPAGE)

    @cherrypy.expose
    def temperatures(self):
        return open("temperatures.html")

    @cherrypy.expose
    def co2(self):
        return open("co2.html")

class ExposedFrontEnd:
    """ This is the server we expose to the WWW """
    
    @cherrypy.expose
    def index(self, cmd=None, task=None):
        """ home page """
        generate_frontend_external()
        return open(HOMEPAGE_EXP)

    @cherrypy.expose
    def temperatures(self):
        return open("temperatures.html")

    @cherrypy.expose
    def co2(self):
        return open("c02.html")

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

def generate_frontend_local(tasks):
    """ We generate this homepage to show up to date task info """
    now = datetime.datetime.utcnow()
    
    with open(HOMEPAGE,"w") as f:
        f.write('<!DOCTYPE html><html lang="en"><body>')
        f.write('UTC Time: %s <br><br>' % str(now))
        f.write('<table>')
        
        f.write('<tr><th>id</th><th>name</th><th>next run</th><th>last run</th><th>last result</th><th>state</th><th>but1</th><th>but2</th></tr>')
        
        for i in range(len(tasks)):
            f.write('<tr>')
            f.write('<td>%d</td>' % i)
            f.write('<td>%s</td>' % tasks[i].task_json["name"])
            f.write('<td>%s</td>' % tasks[i].next_run)
            f.write('<td>%s</td>' % tasks[i].last_run)
            f.write('<td>%s</td>' % tasks[i].last_result)
            if (tasks[i].paused):
                f.write('<td>paused</td>')
            else:
                f.write('<td>running</td>')
            f.write('<td><a href=?cmd=pause&task=%d>(un)pause</a></td>' % i)
            f.write('<td><a href=?cmd=runnow&task=%d>run now</a></td>' % i)
            f.write('</tr>')
        
        f.write('</table>')
        f.write('<br><br><a href="/">Reload</a> . . . . . . . <a href="temperatures">Temp Graph</a> . . . . .  . . . . . <a href="co2">CO2 Graph</a>')
        f.write('<br><br>')
        f.write('</body></html>')

def start_all_tasks():
    for task in tasks:
        task.startstop_task()

def load_tasks():
    # Load Task info from config file
    with open(TASK_JSON_CFG, 'r') as f:
        task_info = json.load(f)

    # Create all our tasks, switch different HomeTasker Children
    for i in range(len(task_info["tasks"])):
        if (task_info["tasks"][i]["type"] == 'out_temp'):
            tasks.append(OutsideTempTask(task_info["tasks"][i]))
        elif (task_info["tasks"][i]["type"] == 'in_temp'):
            tasks.append(IndoorTempPressTask(task_info["tasks"][i]))
        elif (task_info["tasks"][i]["type"] == 'exp_entr'):
            tasks.append(CandaInstructionTask(task_info["tasks"][i]))
        elif (task_info["tasks"][i]["type"] == 'nas_wake'):
            tasks.append(NasWake(task_info["tasks"][i]))
        elif (task_info["tasks"][i]["type"] == 'nas_hdd'):
            tasks.append(NasCheckSmart(task_info["tasks"][i]))
        elif (task_info["tasks"][i]["type"] == 'nas_slp'):
            tasks.append(NasShutdown(task_info["tasks"][i]))
        elif (task_info["tasks"][i]["type"] == 'in_c02'):
            tasks.append(IndoorCO2(task_info["tasks"][i]))
        elif (task_info["tasks"][i]["type"] == 'chck_ip'):
            tasks.append(UpdateIP(task_info["tasks"][i]))
        else:
            tasks.append(BaseTask(task_info["tasks"][i]))

def start_local_server():
    # Start our local server and hope for the best
    load_tasks()
    start_all_tasks()
    generate_frontend_local(tasks)

    local_conf = os.path.join(os.path.dirname(__file__), CHERRY_SERVER_CFG)
    cherrypy.tools.secureheaders = cherrypy.Tool('before_finalize', secureheaders, priority=60)
    cherrypy.quickstart(LocalFrontEnd(), config=local_conf)

def start_exposed_server():
    # Start our external server
    generate_frontend_external()

    conf = os.path.join(os.path.dirname(__file__), CHERRY_SERVER_EXP_CFG)
    cherrypy.tools.secureheaders = cherrypy.Tool('before_finalize', secureheaders, priority=60)
    cherrypy.quickstart(ExposedFrontEnd(), config=conf)

if __name__ == '__main__':
    try:
        if (sys.argv[1] == 'expose'):
            exposed_server = threading.Thread(target=start_exposed_server, daemon=True)
            exposed_server.start()
        else:
            start_local_server()
    
    except IndexError as e:
        print("arg not provided")
        start_local_server()