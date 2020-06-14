import datetime #NOTE: All function time/date calls should use UTC
import threading
import json
from time import sleep

class BaseTask():
    def __init__(self,task_json):
        """
        Generic Task on which new tasks can be created with 
         additional initialization and calling function
        """
        self.task_json = task_json
        self._add_init()
        
        self.paused = True
        self.next_run = None
        self.run_now = False
        self.frequency = None
        self.start_utc = None
        self.end_utc = None
        self.last_run = None
        self.last_result = None
        
        self._import_data()
        self._calc_next_run()
        
        self.mainthread = threading.Thread(target=self._main, daemon=True)
        self.mainthread.start()

    def _add_init(self):
        """ Run additional startup tasks so as not to override init in child """
        pass

    def _import_data(self):
        """ when the task is initialized, we translate the data from the json
            into datetime values """
        if (self.task_json["freq"]):
            self.frequency = datetime.timedelta(minutes=int(self.task_json["freq"]))
        if (self.task_json["start"]):
            self.start_utc = datetime.time(hour=int(self.task_json["start"][0:2]), minute=int(self.task_json["start"][3:5]))
        if (self.task_json["end"]):
            self.end_utc = datetime.time(hour=int(self.task_json["end"][0:2]), minute=int(self.task_json["end"][3:5]))

    def startstop_task(self):
        """ call to toggle between the task being paused and not """
        if (not self.paused):
            self.paused = True
        else:
            self.paused = False

    def trigger_run_now(self):
        """ trigger the function to run in the next minute
            regardless of what days/times it's supposed to run """
        self.run_now = True

    def _calc_next_run(self):
        """ assuming we have just run, calculate when next we should run """
        now = datetime.datetime.utcnow()
        #tasks we always run we just add freq
        if (self.start_utc == None):
            if (self.next_run):
                self.next_run = now + self.frequency
            else:
                #if it's the first time we're running we set our next run
                self.next_run = now
            return
        
        # this is a once a day task
        if (self.frequency == None):
            date = now.date()
            time = self.start_utc
            self.next_run = datetime.datetime.combine(now,time)

            if (now > self.next_run):
                self.next_run += datetime.timedelta(hours=24)

            # now we need to check what day we're supposed to run on
            invalid = 0
            while(invalid < 10):
                if (self.task_json["days"][self.next_run.weekday()] == 1):
                    return
                else:
                    self.next_run += datetime.timedelta(hours=24)
                    invalid +=1
            
            raise Exception("No valid day found")

                
    def _should_run(self):
        """ Check if we are supposed to run now """
        now = datetime.datetime.utcnow()
        #print("next: %s now: %s" % (str(self.next_run), str(now)))
        
        if (not self.paused):
            if (self.run_now):
                self.next_run = now
                self.run_now = False
                
            if (now >= self.next_run): 
                return True

        return False
    
    def _main(self):
        """ The class's main thread, loops constantly """
        while(True):
            if(self._should_run()):
                self._intern_funct()
                self.last_run = datetime.datetime.utcnow()
                self._calc_next_run()
            sleep(61)#seconds
                
    def _intern_funct(self):
        """ This is where we put what we want the task to actually do """
        print("%s task run" % self.task_json["name"])
        self.last_result = "ahh yeah"