#!/usr/bin/env python3
# coding=utf-8
"""接收 GitHub 或 Gitee 的 Webhooks 并运行工具将仓库中的 Markdown 生成为 HTML 静态页面
支持的页面生成工具: Hugo、mdBook
"""
import os
import sys
import argparse
import logging

from pathlib import Path

from logging.handlers import RotatingFileHandler

from flask import Flask
from flask import request

import util

from github_hook import GitHubHook
from gitee_hook import GiteeHook
from hugo_cmd import HugoCmd
from mdbook_cmd import MdbookCmd

"""gunicorn -w 1 -b 127.0.0.1:5001 -e GIT_URL=<clone-url> \
      -e TOOL_TYPE=<hugo or mdbook> -e SECRET_KET=<Webhooks key> main:app
"""

# 日志目录
LOG_DIR = './logs'
# 日志级别
LOG_LEVEL = logging.DEBUG
# 程序名
PROG_NAME = 'git-webhook-html'
# 支持工具的种类
TOOL_TYPES = ('hugo', 'mdbook')

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# 日志配置
log_path = os.path.join(script_dir, LOG_DIR)
if not Path(log_path).is_dir():
    Path(log_path).mkdir()
log_file = Path(log_path) / Path(PROG_NAME)
log_file = '{}.log'.format(str(log_file))

log = logging.getLogger('')
log.setLevel(LOG_LEVEL)
log_handler = RotatingFileHandler(log_file, 
                                  maxBytes=32*1024*1204, 
                                  backupCount=2, 
                                  encoding='utf-8')
log_handler.setLevel(LOG_LEVEL)
log_formatter = logging.Formatter(fmt='%(asctime)s - %(name)s [%(levelname)s] %(message)s')
log_handler.setFormatter(log_formatter)
log.addHandler(log_handler)
log.addHandler(logging.StreamHandler())

# 参数处理
if not os.getenv('GIT_URL'):
    log.error("Environment variable GIT_URL does not exist.")
    sys.exit(-1)
repo_url = os.getenv('GIT_URL')
if not os.getenv('TOOL_TYPE'):
    log.error("Environment variable TOOL_TYPE does not exist.")
    sys.exit(-1)
tool_type = os.getenv('TOOL_TYPE')
if tool_type not in TOOL_TYPES:
    log.error("Unsupported tool type: %s, supports hugo and mdbook", tool_type)
    sys.exit(-1)
secret_key = ''
if os.getenv('SECRET_KEY'):
    secret_key = os.getenv('SECRET_KEY')

# 检查 git 命令
stat = util.execute_command('git --version')
if not stat or stat.returncode != 0:
    sys.exit(-1)

# 初始化仓库
local_dir = util.get_repo_from_url(repo_url)
if not local_dir:
    log.error("input repository url error: %s", repo_url)
    sys.exit(-1)
if os.path.exists(local_dir):
    if not os.path.isdir(local_dir):
        log.error("File exists in %s", local_dir)
        sys.exit(-1)
    # 更新仓库
    stat = util.execute_command('cd {} && git pull --recurse-submodules'.format(local_dir))
    if not stat or stat.returncode != 0:
        sys.exit(-1)
    log.info("repository %s updated.", repo_url)
else:
    # 初次克隆仓库
    stat = util.execute_command('git clone --recursive {}'.format(repo_url))
    if not stat or stat.returncode != 0:
        sys.exit(-1)
    log.info('repository %s initialized.', repo_url)
    
# 设置静态页面输出目录
if os.getenv('OUTPUT') and os.path.isdir(os.getenv('OUTPUT')):
    output_path = os.getenv('OUTPUT')
else:
    output_dir = '%s-output' % local_dir
    output_path = os.path.join(script_dir, output_dir)

# 初始化文档
if tool_type == 'hugo':
    cmd_tool = HugoCmd(local_dir, output_path)
    if not cmd_tool.build():
        log.error("Failed to initialize hugo document")
        sys.exit(-1)
    log.info("hugo document is initialized")
elif tool_type == 'mdbook':
    cmd_tool = MdbookCmd(local_dir, output_path)
    if not cmd_tool.build():
        log.error("Failed to initialize mdbook document")
        sys.exit(-1)
    log.info("mdbook document is initialized")
else:
    sys.exit(-1)

# 初始化 webhooks 服务
app = Flask(__name__)
app.logger.setLevel(LOG_LEVEL)

@app.route("/api/docs", methods=["POST"])
def merged_deploy():
    for k, _ in request.headers:
        if 'X-Github' in k:
            git_hook = GitHubHook(secret_key, request, local_dir)
            break
        if 'X-Gitee' in k:
            git_hook = GiteeHook(secret_key, request, local_dir)
            break
    else:
        return {'message': 'headers error!'}, 400


    """WebHooks 处理
    https://docs.github.com/en/webhooks-and-events/webhooks/webhook-events-and-payloads
    https://gitee.com/help/articles/4186#article-header0
    """
    if not git_hook.header_check():
        return {'message': 'headers error!'}, 400
    
    if not git_hook.signature():
        return {'message': 'hook auth error!'}, 400
    
    if not git_hook.body_filter():
        return {'message': 'body error!'}, 400
    
    # 执行生成文档操作
    # 首先更新仓库
    stat = util.execute_command('cd {} && git pull --recurse-submodules'.format(local_dir))
    if not stat or stat.returncode != 0:
        log.error("Failed to update repository: %s", repo_url)
        return {'message': 'repo error!'}, 500
    log.info("repository %s updated.", repo_url)
    if not cmd_tool.build():
        log.error("Failed to generate %s document", tool_type)
        return {'message': 'doc error!'}, 500
    log.info("%s document is generated", tool_type)
    return {'message': 'success'}, 201

