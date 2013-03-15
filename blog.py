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


site_config = {
    "title" : "歪鱼",
    "url" : """http://bb.yyu.me""",
    "post_dir": os.getcwd() + os.sep + 'posts',
}

settings = {
    "static_path": os.path.join(os.path.dirname(__file__), "static"),
    "debug": True,
}

def SingleFileHandler(file_path):
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
        ret['content'] = markdown.markdown(content)
        ret['name'] = file_path.split(os.sep)[-1].split('.')[0]
    return ret
    
class MainHandler(tornado.web.RequestHandler):
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
             
        self.render("template/index.html", title=site_config['title'], url=site_config["url"], articles = articles, prev=prev, pnext=pnext, prevnum=p-3, nextnum=p+3)

class ArticleHandler(tornado.web.RequestHandler):
    def get(self, article_id):
        post_path = site_config["post_dir"] + os.sep + article_id.replace('.','') + '.md'
        article = SingleFileHandler(post_path)
        
        self.render("template/article.html", title=site_config['title'], url=site_config["url"], article = article)


class NotFoundHandler(tornado.web.RequestHandler):
    def prepare(self):
        self.set_status(404)
        self.render("template/404.html")

class RSSHandler(tornado.web.RequestHandler):
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

class EditorHandler(tornado.web.RequestHandler):
    def get(self):
        return self.render('template/editor.html')

class SaveArticleHandler(tornado.web.RequestHandler):
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
        
        today_file_number = 1
        for f in files:
            file_date = '-'.join(f.split('-')[:3])
            print file_date, today
            if file_date == today:
                today_file_number += 1

        file_sn = today + '-' + str(today_file_number)
        file = open('posts/%s-%s.md'%(file_sn, filename), 'w')
        file.write(u'%s'%_extra_info)
        file.write(content)
        file.close()
        return self.finish({'res': 'ok'})
        
class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/article/(.*)", ArticleHandler),
            (r"/.*\.xml",RSSHandler),
            (r"/save", SaveArticleHandler),
            (r"/editor", EditorHandler),
            (r"/.*", NotFoundHandler),
        ]
        tornado.web.Application.__init__(self, handlers, **settings)

if __name__ == "__main__":
    port = sys.argv[1]
    http_server = tornado.httpserver.HTTPServer(Application(), xheaders=True)
    http_server.listen(port)
    tornado.autoreload.start()
    RSSMaker()
    tornado.ioloop.IOLoop.instance().start()
