#coding=utf8


def login_required(func):
    def new_func(*argc, **argkw):
        #return func(*argc, **argkw)
        # check if the user logined
        request = argc[0] or argkw.get('request')
        if not request.session.get('user'):
            return request.redirect('/account/login')
        else:
            return func(*argc, **argkw)
    return new_func
