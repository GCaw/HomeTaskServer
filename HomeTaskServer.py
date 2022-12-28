import json
import cherrypy
import datetime
import sys
import importlib
import logging
import subprocess
from os import path

from tasks.task_base import BaseTask

CHERRY_SERVER_CFG = path.join("config","cherry_config.conf")
TASK_JSON_CFG = path.join("config","task_config.json")
HOMEPAGE = path.join("generated_files","index.php")

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
        return open(path.join("generated_files","temperatures.html"))
    
    @cherrypy.expose
    def temperatures_long(self):
        return open(path.join("generated_files","temperatures_long.html"))

    @cherrypy.expose
    def co2(self):
        return open(path.join("generated_files","co2.html"))
    
    @cherrypy.expose
    def record_temp(self, temp, crypto):
        if (crypto == 'aawqpeiorj2590-34'):
            for task in tasks:
                if (task.task_json["name"] == 'inside_temp'):
                    temp = float(temp)
                    task.save_add_temp(temp)
                    return "Yay"
            return "almost"                
        return "OH NO!"            

def secureheaders():
    headers = cherrypy.response.headers
    headers['X-Frame-Options'] = 'DENY'
    headers['X-XSS-Protection'] = '1; mode=block'
    headers['Content-Security-Policy'] = "default-src='self'"

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
        f.write('<br><br><a href="/">Reload</a> . . . . . . . <a href="temperatures">Temp Graph</a> . . . . .  . . . . . <a href="co2">CO2 Graph</a> . . . . . . . <a href="temperatures_long">Temp Graph Long</a>')
        f.write('<br><br>')
        f.write('</body></html>')

def start_all_tasks():
    for task in tasks:
        task.startstop_task()

def load_tasks():
    # Load Task info from config file
    with open(TASK_JSON_CFG, 'r') as f:
        task_info = json.load(f)

    # Create all our tasks dynamically
    for i in range(len(task_info["tasks"])):
        try:
            # import module specified in json
            mod = importlib.import_module(task_info["tasks"][i]["module"])
            # Get the class from the module
            task = getattr(mod,task_info["tasks"][i]["class"])
            # and add the task to the task list
            tasks.append(task(task_info["tasks"][i]))

        except Exception as e:
            tasks.append(BaseTask(task_info["tasks"][i]["name"]))
            print("Error importing %s: %s" % task_info["tasks"][i]["module"], e)

def start_local_server():
    ''' Start our local server and hope for the best '''

    new_log_file = f"{datetime.datetime.now()}.log"
    log_format='%(asctime)s %(levelname)s:%(message)s'
    logging.basicConfig(filename=new_log_file, format=log_format, level=logging.DEBUG)
    load_tasks()
    start_all_tasks()
    generate_frontend_local(tasks)

    local_conf = path.join(path.dirname(__file__), CHERRY_SERVER_CFG)
    cherrypy.tools.secureheaders = cherrypy.Tool('before_finalize', secureheaders, priority=60)
    cherrypy.quickstart(LocalFrontEnd(), config=local_conf)

if __name__ == '__main__':

    for i in range(len(sys.argv)):
        if (sys.argv[i] == "--expose"):
            p = subprocess.Popen(['python', 'HomeTaskServerExtern.py'])
                
    print("Starting Local Server")
    start_local_server()
