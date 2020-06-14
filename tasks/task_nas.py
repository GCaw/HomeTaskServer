
import ping3
import paramiko
from wakeonlan import send_magic_packet
from time import sleep

from tasks.task_base import GenericTask
from tasks.config import NAS_MAC_ADDRESS, NAS_IP_ADDRESS, NAS_SSH_USERNAME, NAS_SSH_PASSWORD

class NasWake(GenericTask):
    """
    Task to send a wake on lan command to local NAS.
    """
    def _add_init(self):
        """ Run additional startup tasks so as not to override init in child """
        pass
                
    def _intern_funct(self):
        """ This is where we put what we want the task to actually do """
        not_awake = True
        attempts = 0
        while (not_awake):
            send_magic_packet(NAS_MAC_ADDRESS)
            sleep(60) #wait a minute for PC to turn on
            
            try:
                r = ping3.ping(NAS_IP_ADDRESS)
            except Exception as e:
                print(e)
                attemps = 3
                r = None

            if ((not r)
            or (r == False)):
                # couldn't contact NAS
                self.last_result = "No response from NAS"
                attempts += 1
                if (attempts == 3):
                    # we time out and give up
                    not_awake = False
            else:
                not_awake = False
                self.last_result = "NAS woken up"


class NasCheckSmart(GenericTask):
    """
    Task to check NAS SMART data
    """
    def _add_init(self):
        """ Run additional startup tasks so as not to override init in child """
        pass
                
    def _intern_funct(self):
        """ This is where we put what we want the task to actually do """
        print("%s task run" % self.task_json["name"])
        self.last_result = "ahh yeah"

    def ssh_stuff(self):
        client = paramiko.SSHClient()
        client.load_host_keys("nas_ssh_key")
        client.set_missing_host_key_policy(paramiko.RejectPolicy)
        client.connect(NAS_IP_ADDRESS, username=NAS_SSH_USERNAME, password=NAS_SSH_PASSWORD)

        res = client.exec_command()
        res[1].read()

class NasShutdown(GenericTask):
    """
    Task to trigger a shutdown command on local NAS
    """
    def _add_init(self):
        """ Run additional startup tasks so as not to override init in child """
        pass
                
    def _intern_funct(self):
        """ This is where we put what we want the task to actually do """
        try:
            client = paramiko.SSHClient()
            client.load_host_keys("tasks/nas_ssh_key")
            client.set_missing_host_key_policy(paramiko.RejectPolicy)
            client.connect(NAS_IP_ADDRESS, username=NAS_SSH_USERNAME, password=NAS_SSH_PASSWORD)

            transport = client.get_transport()
            session = transport.open_session()
            session.set_combine_stderr(True)
            session.get_pty()
            session.exec_command("sudo -k shutdown -h 1")
            stdin = session.makefile('wb', -1)
            stdout = session.makefile('rb', -1)
            stdin.write("%s\n" % NAS_SSH_PASSWORD)
            stdin.flush()

            res = stdout.read().decode("utf-8").split("\r\n")[2]
            client.close()
            self.last_result = res
        except TimeoutError as e:
            self.last_result = "Timeout on shutdown attempt"
            print(e)