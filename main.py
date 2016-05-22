#! /usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Created on 2016年5月22日

@author: GiliGili eye
'''


import time
import urllib.request
import json
import re
import sys
import os
import cookielib
import MySQLdb
import chardet
reload(sys)
sys.setdefaultencoding('utf-8')

tw_new_submit_id = 1


class Wooyun(object):
    'Wooyun Taiwan Crawler'

    def __init__(self):
        self.main()

    def crawl_new_submit(self):
        global tw_new_submit_id
        cj = cookielib.LWPCookieJar()
        cookie_support = urllib2.HTTPCookieProcessor(cj)
        opener = urllib2.build_opener(cookie_support, urllib2.HTTPHandler)
        urllib2.install_opener(opener)
        # 以上一段是讲获取到的cookie与urlopen绑定,不然302跳转一直是大陆地区首页的
        url = 'http://www.wooyun.org/bugs/new_submit/'
        # Wooyun的最新回报页面
        url_move = 'http://www.wooyun.org/area/3'
        # area1为大陆地区，2为香港地区，3为台湾地区,通过这个区域的302跳转到首页
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.152 Safari/537.36 LBBROWSER"
        }
        # http头
        index_request_move = urllib2.Request(url=url_move, headers=headers)
        index_respone_move = urllib2.urlopen(index_request_move)
        # 请求area区域，跳转到相应的index页面
        index_request = urllib2.Request(url=url, headers=headers)
        index_respone = urllib2.urlopen(index_request)
        # 请求最新回报页面，因为是带着cookie去访问的，所以会自动跳转到相应区域的最新回报页面
        respone_data = index_respone.read()
        title_pattern = re.compile(r'bugs/wooyun.*\d">(.*?)</a>')
        # 匹配出文章标题
        url_pattern = re.compile(r'<td><a href="(/\S+/\S+-.*\d)">.*?</a>')
        # 匹配出文章url的相对路径
        title_list = re.findall(title_pattern, respone_data)
        # 将页面所有匹配到的标题放进一个数组里
        url_list = re.findall(url_pattern, respone_data)
        # 将页面所有匹配到的url相对路径放进一个数组里
        conn = MySQLdb.connect(
            host='localhost', port=3306, user='root', passwd='lu19930913', db='Wooyun_tw', charset='utf8')
        # 连接到数据库
        cur = conn.cursor()
        # 创建一个浮标，后面对数据库的操作都是调用这个cur的。
        for self.title_data, url_relative_data in zip(title_list, url_list):
                # 遍历这两个数组里的两个值
            self.url_absolute_data = "http://www.wooyun.org%s" % (
                url_relative_data)
            # 将相对路径转换成绝对路径（拼接起来的）
            # print u"文章标题：" + self.title_data, u"文章url：" + self.url_absolute_data  输出内容
            # 输出
            select_url = cur.execute(
                "select * from tw_new_submit where url = '%s'" % (self.url_absolute_data))
            # 查找数据库里是否已经有了相同url的数据，如果是空的那么会返回一个none值，在python里这个值是为Fales。
            while True:
            # 因为怕ID冲突所以先开启一个循环。
                select_id = cur.execute(
                    "select * from tw_new_submit where id = '%s'" % (tw_new_submit_id))
                # 查询表里的字段ID，ID为主键不能重复，默认值为最上面的1
                # print select_id 输出是否有
                if select_id:
                    # 如果有
                    tw_new_submit_id += 1
                    # 那么就自增1
                    print('ID冲突，自增1')
                else:
                    break
            # print tw_new_submit_id
            # print 'ID无冲突，可以用'
            if not select_url:
                # 如果url不冲突，那么执行下面的代码
                bugs_detail_request = urllib2.Request(
                    url=self.url_absolute_data, headers=headers)
                bugs_detail_respone = urllib2.urlopen(bugs_detail_request)
                bugs_detail_data = bugs_detail_respone.read()
                # 获取绝对路径的网页内容
                # print chardet.detect(bugs_detail_data)
                bugs_detail_pattern = re.compile(
                    r'wybug_date\'>(.*?)</h3>.\n.*?<h3.*?>(.*?)</h3>.\n.*?<h3.*?>(.*?)</h3>')
                bugs_detail = re.findall(bugs_detail_pattern, bugs_detail_data)
                # 匹配出我需要的内容
                # print bugs_detail
                for bugs_detail_weneed in bugs_detail:
                    # 历遍我需要的内容
                    bugs_detail_pattern_kill = re.compile(
                        r'\t+')
                    # 用正则匹配出\t标签
                    self.subtime = re.sub(
                        bugs_detail_pattern_kill, '', bugs_detail_weneed[0])
                    self.optime = re.sub(
                        bugs_detail_pattern_kill, '', bugs_detail_weneed[1])
                    self.bug = re.sub(
                        bugs_detail_pattern_kill, '', bugs_detail_weneed[2])
                    # 将\t标签换成空的，就是删除\t
                    print(tw_new_submit_id)
                    print(u'%s\n%s\n%s\n%s\n%s' % (self.title_data, self.url_absolute_data, self.subtime, self.optime, self.bug))
                    cur.execute(
                        "insert into tw_new_submit values('%d','%s','%s','%s','%s','%s')" % (
                            tw_new_submit_id, self.title_data, self.url_absolute_data, self.subtime, self.optime, self.bug))
                    # 将数据插入数据库
                    print('爬完一个页面了，好累了QAQ，休息一会会儿~' + '时间：' + str(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(time.time())))))
                    tw_new_submit_id += 1
                    # 使ID值+1,以便下次插入
                    time.sleep(5)
                    #休眠五秒
                    print('继续下一个！')
            else:
                continue
                # 如果数据库里已经有这个URL的数据了，那么就跳过这个url，继续下一个。
        # cur.execute("delete from tw_new_submit where id<=30")
        cur.close()
        # 关闭浮标
        conn.commit()
        #写入数据，不执行这句代码的话，不会将数据真正的写入数据库的。
        conn.close()
        # 关闭数据库连接
        print('没有获取到新的数据，正在睡眠中zzz' + '时间：' + str(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(time.time())))))
        time.sleep(300)
        print('睡眠完毕，reloading...' + '时间：' + str(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(time.time())))))

    # def

    def main(self):
        while True:
            self.crawl_new_submit()

a = Wooyun()