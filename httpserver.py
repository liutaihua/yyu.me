#coding=utf8
import tornado.ioloop
import tornado.autoreload
import tornado.httpserver
import tornado.web
import string, os, sys
import markdown
import codecs
import PyRSS2Gen
import datetime

import sys
reload(sys)
sys.setdefaultencoding('utf8')

from config.web_config import site_config, settings
from config.web_config import admin_list
from common.base_httphandler import BaseHandler
from common import session
from common.decorator import login_required
from common.util import get_mc

mc = get_mc()


def SingleFileHandler(file_path, keep_original=False):
    f = codecs.open(file_path, mode='r', encoding='utf8')
    lines = []
    try:
        lines = f.readlines()
    except:
        pass
    f.close()
    
    ret = {}
    title = ''
    date = ''
    index = 1

    for line in lines[1:]:
        index += 1
        if line.find('Title: ') == 0:
            title = line.replace('Title: "','')[0:-2]
            #title = line.replace('Title: ','')[0:-1]
            title = '<h3><font color="green">' + title + '</font></h3>'
        if line.find('Date: ') == 0:
            date = line.replace('Date: ','')[0:-1]
        if line.find('--') == 0:
            break

    content = u'';
    for line in lines[index:]:
        content += line
        
    if title:
        ret['title'] = title
        ret['date'] = date
        if keep_original:
            ret['content'] = content
        else:
            ret['content'] = markdown.markdown(content)
        ret['name'] = file_path.split(os.sep)[-1].split('.')[0]
    return ret
    
class MainHandler(BaseHandler):
    def get(self):
        articles = []
        post_dir = site_config["post_dir"]
        file_list = []
        files = os.listdir(post_dir)

        p = int(self.get_argument('p','0'))

        for f in files:
            file_list.append(post_dir + os.sep + f)
        file_list.sort(reverse=True)
        for single_file in file_list[p:p+3]:
            article = SingleFileHandler(single_file)
            if article: articles.append(article)

        if p > 2:
            prev = True
        else:
            prev = False

        if p + 4 <= len(file_list):
            pnext = True
        else:
            pnext = False
             
        self.render("index.html", title=site_config['title'], url=site_config["url"], articles = articles, prev=prev, pnext=pnext, prevnum=p-3, nextnum=p+3)

class ArticleHandler(BaseHandler):
    def get(self, article_id):
        post_path = site_config["post_dir"] + os.sep + article_id.replace('.','') + '.md'
        article = SingleFileHandler(post_path)
        
        self.render("article.html", title=site_config['title'], url=site_config["url"], article = article)


class NotFoundHandler(BaseHandler):
    def prepare(self):
        self.set_status(404)
        self.render("404.html")

class RSSHandler(BaseHandler):
    def get(self):
        f = open("rss.xml", "r")
        self.write(f.read())
        f.close()

def RSSMaker():
    articles = []
    post_dir = site_config["post_dir"]
    file_list = []
    files = os.listdir(post_dir)
    
    for f in files:
        file_list.append(post_dir + os.sep + f)
    file_list.sort(reverse=True)
    
    for single_file in file_list:
        article = SingleFileHandler(single_file)
        if article: articles.append(article)
        
    rss_items = []
    for article in articles:
        link = site_config["url"]+"/article/"+article["name"]
        year = article["date"][0:4]
        month = article["date"].split('-')[1]
        day = article["date"].split('-')[2].split(' ')[0]
        hour = article["date"].split('-')[2].split(' ')[1].split(':')[0]
        minute = article["date"].split('-')[2].split(' ')[1].split(':')[1]
        rss_item = PyRSS2Gen.RSSItem(
            title = article["title"],
            link = link,
            description = article["content"],
            guid = PyRSS2Gen.Guid(link),
            pubDate = datetime.datetime(
                year = int(year),
                month = int(month),
                day = int(day),
                hour = int(hour),
                minute = int(minute),
                second = 0,
        ))
        rss_items.append(rss_item)
        
    rss = PyRSS2Gen.RSS2(
        title = site_config["title"],
        link = site_config["url"],
        description = "",
        lastBuildDate = datetime.datetime.utcnow(),
        items = rss_items)

    rss.write_xml(open("rss.xml", "w"))

class EditorHandler(BaseHandler):
    @login_required
    def get(self):
        filename = self.get_argument('filename', '')
        post_dir = site_config["post_dir"]
        files = os.listdir(post_dir)

        article_title = ''
        if filename != '':
            for fname in files:
                if filename in fname:
                    filename = fname.strip('.md')
                    post_path = site_config["post_dir"] + os.sep + fname
                    article = SingleFileHandler(post_path)
                    article_title = article['title']
                    break
        return self.render('editor.html', files=files, edit_file=filename, article_title=article_title)

class SaveArticleHandler(BaseHandler):
    def post(self):
        filename = self.get_argument('filename')
        article_subject = self.get_argument('subject')
        content = self.request.body

        today_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        _extra_info = """--
layout: post
Title: "%s"
Date: %s
comments: true
categories: notes
--

"""%(article_subject, today_time)

        post_dir = site_config["post_dir"]
        files = os.listdir(post_dir)
        for fname in files:
            if filename in fname:
                filename = fname
                break
        else:
            today_file_number = 1
            for f in files:
                file_date = '-'.join(f.split('-')[:3])
                if file_date == today:
                    today_file_number += 1

            file_sn = today + '-' + str(today_file_number)
            filename = '%s-%s.md'%(file_sn, filename)
        #file = open('posts/%s-%s.md'%(file_sn, filename), 'w')
        file = open('posts/%s'%filename, 'w')
        file.write(u'%s'%_extra_info)
        file.write(content)
        file.close()
        return self.finish({'res': 'ok'})


class LoginHandler(BaseHandler):
    def get(self, action):
        if action == 'logout':
            self.session.clear()
            self.session.save()
            return self.redirect('/')
        self.render('login.html')

    def post(self, action):
        if action == 'login':
            username = self.get_argument('username')
            password = self.get_argument('password')
            if (username, password) not in admin_list:
                return self.redirect('/account/login')
                return self.finish('you are not admin')
            else:
                self.session['user'] = username
                self.session.save()
                return self.redirect('/')

class ImportFileHandler(BaseHandler):
    def get(self):
        file = self.get_argument('filename')
        file_path = site_config["post_dir"] + os.sep + file
        article = SingleFileHandler(file_path, keep_original=True)
        content = article['content']
        return self.finish(content)
   
class GHandler(BaseHandler):
    def get(self):
        return self.render('googled4ec9ff1a19199b5.html')

class NewBlogLikeFeatureHandler(BaseHandler):
    def get(self, action):
        shortname = self.get_argument('shortname')
        identifier = self.get_argument('identifier')
        name = self.get_argument('name')
        user = identifier.split(':')[-1]
        is_liked_key = str("%s@%s" % (user, name))
        artical_liked_count_key = str(name)
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Methods', 'POST,GET')
        if action == 'like_count':
            like_count = mc.get(artical_liked_count_key) or 0
            is_user_liked = mc.get(is_liked_key) or False
            return self.finish({"liked": is_user_liked, "count":like_count,"user": user})

    def post(self, action):
        shortname = self.get_argument('shortname')
        identifier = self.get_argument('identifier')
        name = self.get_argument('name')
        user = identifier.split(':')[-1]
        is_liked_key = str("%s@%s" % (user, name))
        artical_liked_count_key = str(name)
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Methods', 'POST,GET')
        if action == 'like':
            like_count = mc.get(artical_liked_count_key) or 0
            like_count += 1
            is_user_liked = mc.get(is_liked_key) or False
            mc.set(artical_liked_count_key, like_count)
            return self.finish({"liked": True, "count": like_count, "user": user})
        elif action == 'unlike':
            like_count = mc.get(artical_liked_count_key) or 0
            like_count -= 1
            is_user_liked = mc.get(is_liked_key) or False
            mc.set(artical_liked_count_key, like_count)
            return self.finish({"liked": False, "count": is_user_liked,"user": user})
        
class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/v1/(.*)", NewBlogLikeFeatureHandler),
            (r"/", MainHandler),
            (r"/googled4ec9ff1a19199b5.html", GHandler),
            (r"/article/(.*)", ArticleHandler),
            (r"/importfile", ImportFileHandler),
            (r"/.*\.xml",RSSHandler),
            (r"/save", SaveArticleHandler),
            (r"/editor", EditorHandler),
            (r"/account/(.*)", LoginHandler),
            (r"/.*", NotFoundHandler),
        ]
        settings.update(dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates")
        ))
        tornado.web.Application.__init__(self, handlers, **settings)
        self.session_manager = session.TornadoSessionManager(settings["session_secret"], settings["session_dir"])

if __name__ == "__main__":
    port = sys.argv[1]
    http_server = tornado.httpserver.HTTPServer(Application(), xheaders=True)
    print 'Listen %s ...'%port
    http_server.listen(port)
    tornado.autoreload.start()
    RSSMaker()
    tornado.ioloop.IOLoop.instance().start()
