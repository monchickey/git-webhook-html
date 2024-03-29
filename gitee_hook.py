# coding=utf-8
import hmac
import time
import base64
import logging

from urllib.parse import quote_plus

import flask

log = logging.getLogger(__name__)

class GiteeHook:
    """Gitee Webhooks 处理
    """
    def __init__(self, secret: str, req: flask.Request, repo_name: str) -> None:
        """Gitee Webhooks 处理类初始化变量
        Args:
            secret: 设定的签名密钥
            req: HTTP 请求内容
            repo_name: 本地仓库名称，便于进行校验
        """
        self.__header_event = 'X-Gitee-Event'
        self.__header_signature = 'X-Gitee-Token'
        self.__header_timestamp = 'X-Gitee-Timestamp'
        self.__secret = secret
        self.__headers = req.headers
        self.__request = req
        self.__repository_name = repo_name
        # 请求和接收时的时间戳最大限制 单位: ms
        self.__timestamp_limit = 3600000

    def header_check(self) -> bool:
        """Webhooks Header 请求正确性检查
        """
        if (self.__header_event not in self.__headers or 
            self.__headers[self.__header_event] != 'Push Hook'):
            return False
        if self.__header_signature not in self.__headers:
            return False
        if self.__header_timestamp not in self.__headers:
            return False
        signature_enc = self.__headers[self.__header_signature]
        if ((self.__secret and not signature_enc) or 
            (not self.__secret and signature_enc)):
            return False
        if not self.__headers[self.__header_timestamp].isdigit():
            return False
        
        current_timestamp = int(round(time.time() * 1000))
        if abs(current_timestamp - int(self.__headers[self.__header_timestamp])) > self.__timestamp_limit:
            return False
        
        return True
    
    def signature(self) -> bool:
        """Webhooks 签名校验
        """
        if self.__secret and self.__headers[self.__header_signature]:
            payload = '{}\n{}'.format(self.__headers[self.__header_timestamp], 
                                      self.__secret).encode('utf-8')
            # 计算 Base64 编码的 hmac sha256 字符串
            h = hmac.new(self.__secret.encode('utf-8'), payload, digestmod='sha256')
            return hmac.compare_digest(base64.b64encode(h.digest()).decode('utf-8'), 
                                       self.__headers[self.__header_signature])
        return True
    
    def body_filter(self) -> bool:
        """Webhooks 请求正文处理
        """
        try:
            r = self.__request.get_json()
            if not r:
                log.error("Json body is empty!")
                return False
            repository = r['repository']
            if repository['name'] != self.__repository_name:
                log.error("Repository name does not correspond! name: %s local: %s", 
                             repository['name'], self.__repository_name)
                return False
            log.info("Repository name: {} url: {}".format(
                repository['name'], repository['url']))
            if 'commits' in r and r['commits']:
                log.info("Current commits count: %d", len(r['commits']))
                for i, commit in enumerate(r['commits']):
                    log.info("commit %d time: %s content: %s", 
                            i + 1, 
                            commit['timestamp'], 
                            commit['message'])
            return True
        except Exception as e:
            log.error("json body filter error: %s", e)
            return False
