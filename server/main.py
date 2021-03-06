#! /usr/bin/env python
# coding=utf-8

import webapp2
import logging
import json

from google.appengine.api import urlfetch

import lib

class MainPage(webapp2.RequestHandler):
    def get(self):
        text = '''<p>This version of keepagent server use <strong>%s</strong> protocol.</p>
        <p>请检查您的客户端是否使用了同一协议。</p>''' % lib.protocol

        self.response.headers['Content-Type'] = 'text/html; charset=UTF-8'
        self.response.write(text)
    
    def post(self):
        #记录一个是否加密的状态变量
        is_crypted = int(self.request.body[0])

        req_body = lib.decrypt(self.request.body)
        req_body = lib.loadDict(req_body)

        method = getattr(urlfetch, req_body.command)

        # 如超时则自动重试4次，4次失败后，GAE会抛错并返回给client 500错误。
        for dl in lib.deadlineRetry:
            try:
                res = urlfetch.fetch(url=req_body.path,
                                     payload=lib.atob(req_body.payload),
                                     method=method,
                                     headers=json.loads(req_body.headers),
                                     follow_redirects=False,
                                     deadline=dl,
                                     validate_certificate=True,
                                     )
            except urlfetch.DownloadError, e:
                logging.error(u'下载错误: %s' % e)
            else:
                break #没有抛出任何异常则跳出循环

        result = {
            'status_code': res.status_code, # int
            # TODO: If there are multiple headers with the same name, their values will be joined into a single comma-separated string. If the values already contained commas (for example, Set-Cookie headers), you may want to use header_msg.get_headers(header_name) to retrieve a list of values instead.
            'headers': json.dumps(dict(res.headers)), 
            'content': lib.btoa(res.content), # str
        }

        result = lib.dumpDict(result)

        if is_crypted:
            result = lib.encrypt(result)
        else:
            result = '0' + result
        
        self.response.write(result)




class UpdatePage(webapp2.RequestHandler):
    def get(self):
        text = urlfetch.fetch(url='https://raw.github.com/alsotang/keepagent/master/update_message').content

        self.response.headers['Content-Type'] = 'text/html; charset=UTF-8'
        self.response.write(text)

app = webapp2.WSGIApplication([(r'/getupdate', UpdatePage),
                               (r'/.*', MainPage)])
