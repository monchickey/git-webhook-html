# coding=utf-8
import logging

import util

log = logging.getLogger(__name__)

class HugoCmd:
    def __init__(self, src_dir, output_dir) -> None:
        self.__src_dir = src_dir
        self.__output_dir = output_dir
        # Hugo 工具命令
        self.__doc_command = 'hugo -d {target}'

    def build(self) -> bool:
        stat = util.execute_command('hugo version')
        if not stat or stat.returncode != 0:
            return False
        hugo_command = self.__doc_command.format(target=self.__output_dir)
        stat = util.execute_command('cd {} && {}'.format(self.__src_dir, hugo_command))
        if not stat or stat.returncode != 0:
            return False
        return True
