# coding=utf-8

import util

class AdditionalCmd:
    def __init__(self, prefix_cmd: str, postfix_cmd: str, workdir: str, relaxed=False):
        self.__prefix_cmd = prefix_cmd
        self.__postfix_cmd = postfix_cmd
        self.__workdir = workdir
        self.__relaxed = relaxed

    def prefix_execute(self):
        if self.__prefix_cmd:
            stat = util.execute_command('cd {} && {}'.format(self.__workdir, 
                                                             self.__prefix_cmd))
            if not self.__relaxed and (not stat or stat.returncode != 0):
                return False
            
        return True
    
    def postfix_execute(self):
        if self.__postfix_cmd:
            stat = util.execute_command('cd {} && {}'.format(self.__workdir, 
                                                             self.__postfix_cmd))
            if not self.__relaxed and (not stat or stat.returncode != 0):
                return False
            
        return True
