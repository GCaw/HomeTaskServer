from os import path

from tasks.task_base import BaseTask
from tasks.helper import IssueHttpRequest, SendMail
from tasks.config import MAIL_ADMIN, IP_CHECKER_URL

class UpdateIP(BaseTask):
    def _add_init(self):
        """ additional startup tasks """
        pass
                
    def _intern_funct(self):
        """ Function called periodically """
        self.CheckIpAddress()

    def CheckIpAddress(self):
        res = IssueHttpRequest(IP_CHECKER_URL)
        print(self.last_result)

        with open(path.join("tasks","web_ip.txt"), "r") as f:
            old = f.read()

        if (res):
            if not (res.text == old):
                
                if SendMail(MAIL_ADMIN, "New Home IP Address", ("new: %s\nold: %s" % (res.text, old))):
                    self.last_result = ("New IP: %s" % res.text)
                    with open(path.join("tasks","web_ip.txt"), "w") as f:
                        f.write(res.text)
                else:
                    
                    self.last_result = "Failed to send new IP: %s" % res.text
            else:
                self.last_result = ("Current IP maintained: %s" % old)