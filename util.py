# coding=utf-8
import os
import sys
import logging
import subprocess

from urllib.parse import urlparse

log = logging.getLogger(__name__)

def get_repo_from_url(url: str) -> str:
    """从 Git URL 中获取仓库名称，即最后一层作为本地目录
    例如: https://github.com/microsoft/DiskANN.git 应返回: DiskANN
    """
    url_res = urlparse(url)
    if not url_res.path:
        return
    repo_name = os.path.splitext(os.path.split(url_res.path)[-1])[0]
    return repo_name

def execute_command(cmd: str) -> subprocess.CompletedProcess:
    try:
        stat = subprocess.run(args=cmd,
                              shell=True,
                              check=True,
                              stdout=sys.stdout,
                              stderr=sys.stderr,
                              timeout=60)
        log.info("The command [%s] was executed successfully! code: %d.", cmd, stat.returncode)
    except subprocess.CalledProcessError as e:
        log.info("Command [%s] failed to execute! error: %s", cmd, e)
    except subprocess.TimeoutExpired as e:
        log.info("Command [%s] execution timed out! error: %s", cmd, e)
    except Exception as e:
        log.info("Command [%s] failed to execute! error: %s", cmd, e)
    else:
        return stat