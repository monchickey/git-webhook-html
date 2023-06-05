# coding=utf-8
import logging

import util

log = logging.getLogger(__name__)

class MdbookCmd:
    def __init__(self, src_dir, output_dir) -> None:
        self.__src_dir = src_dir
        self.__output_dir = output_dir
        # mdBook 工具命令
        self.__doc_command = 'mdbook build {path} -d {target}'

    def build(self) -> bool:
        stat = util.execute_command('mdbook --version')
        if not stat or stat.returncode != 0:
            return False
        mdbook_command = self.__doc_command.format(self.__src_dir, target=self.__output_dir)
        stat = util.execute_command(mdbook_command)
        if not stat or stat.returncode != 0:
            return False
        return True
