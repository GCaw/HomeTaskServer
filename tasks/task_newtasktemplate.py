from tasks.task_base import BaseTask

class GenericTaskTemplate(BaseTask):
    def _add_init(self):
        """ Run additional startup tasks so as not to override init in child """
        pass
                
    def _intern_funct(self):
        """ This is where we put what we want the task to actually do """
        print("%s task run" % self.task_json["name"])
        self.last_result = "ahh yeah"