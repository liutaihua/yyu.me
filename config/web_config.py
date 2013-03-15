#coding=utf8
import os


site_config = {
    "title" : "歪鱼",
    "url" : """http://bb.yyu.me""",
    "post_dir": os.getcwd() + os.sep + 'posts',
}

settings = {
    "static_path": os.path.join(os.path.dirname(__file__), "../static"),
    "debug": True,
    'session_dir': 'sessions',
    'session_secret': 'blabla',
    'cookie_secret': "y+iqu2psQRyVqvC0UQDB+iDnfI5g3E5Yivpm62TDmUU=",
}

admin_list = [
    ('admin', 'defage851230'),
]
