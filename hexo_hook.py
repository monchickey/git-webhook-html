# coding=utf-8
import os
import logging

import util

from additional_cmd import AdditionalCmd

log = logging.getLogger(__name__)

class HexoCmd:
    def __init__(self, src_dir, output_dir, add_cmd: AdditionalCmd) -> None:
        self.__src_dir = src_dir
        self.__output_dir = output_dir
        # Hexo 工具命令
        self.__doc_command = 'hexo clean && hexo generate'
        # 前置后置命令
        self.__additional_cmd = add_cmd

    def build(self) -> bool:
        stat = util.execute_command('hexo version')
        if not stat or stat.returncode != 0:
            return False
        stat = util.execute_command('npm --version')
        if not stat or stat.returncode != 0:
            return False
        
        # 执行前置命令
        if not self.__additional_cmd.prefix_execute():
            return False
        # 生成文档
        stat = util.execute_command('cd {} && npm install && {}'.format(self.__src_dir, self.__doc_command))
        if not stat or stat.returncode != 0:
            return False
        # 同步至目标目录
        sync_static_command = 'cd {} && rsync -av --delete ./public/ {}'.format(self.__src_dir, self.__output_dir)
        stat = util.execute_command(sync_static_command)
        if not stat or stat.returncode != 0:
            return False
        # 执行后置命令
        return self.__additional_cmd.postfix_execute()
