__author__ = 'stefan'
from flask import Flask, request, send_from_directory, session
from common.constants import WEBAPP_USER, WEBAPP_PWD
from string import ascii_letters, digits
from random import SystemRandom

class WebApp(Flask):

    def __init__(self, import_name):
        super().__init__(import_name)
        self.secret_key = ''.join(SystemRandom().choice(ascii_letters+digits) for _ in range(32))

    def is_logged_in(self):
        return 'user' in session

    def auth(self, user, pwd):
        #just a simple auth method. replace with real user authentication
        if user == WEBAPP_USER and pwd == WEBAPP_PWD:
            session['user'] = WEBAPP_USER
            return True
        else:
            return False

    def logout(self):
        #just a simple auth method. replace with real user authentication
        if 'user' in session:
            del session['user']
            return True
        else:
            return False

    def protected_route(self, rule, **options):
        def decorator(f):
            endpoint = options.pop('endpoint', rule)
            def save(*args, **kwargs):
                if self.is_logged_in():
                    return f(*args, **kwargs)
                else:
                    return send_from_directory('web', 'login.html')
            self.add_url_rule(rule, endpoint, save, **options)
            return save
        return decorator

    def get_session(self):
        return session

    def get_request(self):
        return request

    def run(self, host='localhost', port=5000, debug=False, threaded=True,**options):
        super(WebApp, self).run(host=host, port=port, debug=debug, threaded=threaded, **options)


