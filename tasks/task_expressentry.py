import smtplib
from html.parser import HTMLParser
from os import path

from tasks.task_base import BaseTask
from tasks.helper import IssueHttpRequest, SendMail
from tasks.config import MAIL_ADMIN

ADDRESS = "https://www.canada.ca/en/immigration-refugees-citizenship/corporate/mandate/policies-operational-instructions-agreements/ministerial-instructions.html#invitations"

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

class InstructionInfo(object):
    def __init__(self):
        pass
        self.date = None
        self.instr_num = 0
        self.fedwork = 0
        self.fedtrad = 0
        self.canexpe = 0
        self.provnom = 0

class CandaInstructionTask(BaseTask):
    """
    Task to read info on latest Ministerial Instruction and parse it
     to determine number of invitations
    """
    def _add_init(self):
        self.instr_obj = InstructionInfo()
        self._read_last_can_exp()
        
    def _intern_funct(self):
        r = IssueHttpRequest(ADDRESS)
        if (r == None):
            print("ExpressEntry: Result unavailable")
        else:
            self._parse_result(r)

            if (self.instr_obj.instr_num > self.last_instruct):
                SendMail(MAIL_ADMIN, "ExpressEntry Update", self.last_result)
                self.last_instruct = self.instr_obj.instr_num
                self._write_last_can_exp()
            print(self.last_result)

    def _read_last_can_exp(self):
        with open(path.join("tasks","can_exp.txt"), "r") as f:
            self.last_instruct = int(f.read())

    def _write_last_can_exp(self):
        with open(path.join("tasks","can_exp.txt"), "w") as f:
            f.write(str(self.last_instruct))
        
    def _parse_result(self, html):
        html_strip = MLStripper()
        html_strip.feed(html.text)
        html_free_text = html_strip.get_data()
        space_free_text = html_free_text.replace(" ", "")
        space_free_text = space_free_text.replace(",", "")
        outstr = ""

        try:
            ee_n_ind  = space_free_text.find("ExpressEntrysystem#")
            self.instr_obj.instr_num = int(space_free_text[ee_n_ind+19:ee_n_ind+22])
            outstr += ("EE %d" % self.instr_obj.instr_num)
        except ValueError as e:
            print("num: %s" % e)

        try:
            date_ind = space_free_text.find("Datemodified")
            self.instr_obj.date = str(space_free_text[date_ind+14:date_ind+25])
            self.instr_obj.date = self.instr_obj.date.strip()
            outstr += (" Date: %s" % self.instr_obj.date)
        except ValueError as e:
            print("date: %s" % e)

        try:
            fedw_ind = space_free_text.find("(FederalSkilledWorker)")
            self.instr_obj.fedwork = int(space_free_text[fedw_ind+22:fedw_ind+30].strip())
            if not (self.instr_obj.fedwork == 0):
                outstr += (" Fed Work: %d" % self.self.instr_obj.fedwork)
        except ValueError as e:
            print("fed w: %s" % e)

        try:
            cexp_ind = space_free_text.find("(CanadianExperience)")
            self.instr_obj.canexpe = int(space_free_text[cexp_ind+20:cexp_ind+28].strip())
            if not (self.instr_obj.canexpe == 0):
                outstr += (" Can Exp: %d" % self.instr_obj.canexpe)
        except ValueError as e:
            print("can e: %s" % e)

        try:
            fedt_ind = space_free_text.find("(FederalSkilledTrades)")
            self.instr_obj.fedtrad = int(space_free_text[fedt_ind+22:fedt_ind+30].strip())
            if not (self.instr_obj.fedtrad == 0):
                outstr += (" Fed Trade: %d" % self.instr_obj.fedtrad)
        except ValueError as e:
            print("fed t: %s" % e)

        try:
            prov_ind = space_free_text.find("(Provincialnominee)")
            self.instr_obj.provnom = int(space_free_text[prov_ind+19:prov_ind+27].strip())
            if not (self.instr_obj.provnom == 0):
                outstr += (" Prov Nom: %d" % self.instr_obj.provnom)
        except ValueError as e:
            print("prov: %s" % e)

        self.last_result = outstr