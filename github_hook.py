# coding=utf-8
import hmac
import logging

import flask

log = logging.getLogger(__name__)

class GitHubHook:
    """GitHub Webhooks 处理
    """
    def __init__(self, secret: str, req: flask.Request, repo_name: str) -> None:
        """GitHub Webhooks 处理类初始化变量
        Args:
            secret: 设定的签名密钥
            req: HTTP 请求内容
            repo_name: 本地仓库名称，便于进行校验
        """
        self.__header_event = 'X-GitHub-Event'
        self.__header_signature = 'X-Hub-Signature-256'
        self.__secret = secret
        self.__headers = req.headers
        self.__request = req
        self.__repository_name = repo_name

    def header_check(self) -> bool:
        """Webhooks Header 请求正确性检查
        """
        if (self.__header_event not in self.__headers or 
            self.__headers[self.__header_event] != 'push'):
            return False
        if self.__header_signature not in self.__headers:
            return False
        signature_enc = self.__headers[self.__header_signature]
        if ((self.__secret and not signature_enc) or 
            (not self.__secret and signature_enc)):
            return False
        return True
    
    def signature(self) -> bool:
        """Webhooks 签名校验
        """
        if self.__secret and self.__headers[self.__header_signature]:
            payload = self.__request.get_data()
            # 计算 16 进制的 hmac sha256 字符串
            h = hmac.new(self.__secret.encode('utf-8'), payload, digestmod='sha256')
            return hmac.compare_digest("sha256=" + h.hexdigest(), self.__headers[self.__header_signature])
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
            log.info("Repository name: {} url: {} size: {}".format(
                repository['name'], repository['url'], repository['size']))
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
