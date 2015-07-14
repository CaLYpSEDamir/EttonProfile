# coding: utf-8

import os
import json
from datetime import datetime
import uuid

from tornado import web
from tornado import ioloop
from tornado.web import Application
from tornado.websocket import WebSocketHandler

import tasks
import tcelery
import redis
from redis_collections import Dict


tcelery.setup_nonblocking_producer()

r = redis.StrictRedis(host='localhost', port='6379', db='third_etton')

# users id-counter
if not r.get('counter'):
    r.set('counter', 1)

users = Dict(key='users', redis=r)


class BaseHandler(web.RequestHandler):

    @property
    def user_id(self):
        return self.get_cookie("tornado_user_id")

    def get_current_user(self):
        return self.user_id


class MainHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            self.redirect("/login")
            return

        self.render("profile_user.html")

    def post(self):

        user_profile = Dict(
            key='user_profile:{0}'.format(self.user_id),
            redis=r
        )

        user_profile['name'] = self.get_argument('name')
        user_profile['email'] = self.get_argument('email')
        user_profile['phone'] = self.get_argument('phone')
        user_profile['country'] = self.get_argument('country')
        user_profile['city'] = self.get_argument('city')
        user_profile['birth'] = self.get_argument('birth')

        self.finish()


class LoginHandler(BaseHandler):
    def get(self):
        self.render("login.html", reg_url='/registration',
                    login_url='/login', error="")

    def post(self):
        login = self.get_argument('login')
        passw = self.get_argument('password')

        old_one = '{0}:{1}'.format(login, passw)

        if old_one not in users:
            self.render(
                "login.html", reg_url='/registration',
                login_url='/login', error="Нет такой учетной записи", jquery='jquery')
        else:
            self.set_cookie("tornado_user_id", users[old_one])
            self.redirect("/")


class RegHandler(BaseHandler):
    def get(self):
        self.render(
            "registration.html", reg_url='/registration',
            login_url='/login', error="")

    def post(self):
        login = self.get_argument('login')
        passw = self.get_argument('password')

        new_one = '{0}:{1}'.format(login, passw)

        if new_one not in users:
            users[new_one] = r.get('counter')
            self.set_cookie("tornado_user_id", r.get('counter'))

            # increase users id-counter
            r.incr('counter')

            self.redirect("/")
        else:
            self.render(
                "registration.html", reg_url='/registration',
                login_url='/login', error="Учетная запись занята")


CITIES_ENUM = {
    '1': {'1': 'Москва', '2': 'Санкт-Петербург', '3': 'Казань'},
    '2': {'1': 'Нью-Йорк', '2': 'Вашингтон', '3': 'Чикаго'},
    '3': {'1': 'Лондон', '2': 'Ливерпуль', '3': 'Манчестер'},
}


class GetCitiesView(BaseHandler):

    def get(self):
        self.write(json.dumps(CITIES_ENUM.get(self.get_argument('country_id'))))


class GetProfileView(BaseHandler):
    def get(self):
        user_profile = Dict(
            key='user_profile:{0}'.format(self.user_id),
            redis=r
        )
        self.write(json.dumps(dict(user_profile.items())))


class NewEventHandler(BaseHandler):

    def post(self):

        date = self.get_argument('eventDate')
        time = self.get_argument('eventTime')
        text = self.get_argument('eventText')
        try:
            count_date = datetime.strptime(
                date+'#'+time, '%m/%d/%Y#%H:%M')
        except ValueError:
            count_down = 2
            text = u'Ошибка даты! ' + text
        else:
            now = datetime.now()
            if now > count_date:
                count_down = 2
                text = u'Событие в прошлом! ' + text
            else:
                count_down = (count_date - datetime.now()).seconds

        tasks.save_event.apply_async(
            (self.user_id, date, time, text), countdown=count_down,
            callback=self.on_result)

    def on_result(self, response):
        user_id, date, time, text = response.result

        user_events = 'user_events:{0}'.format(user_id)
        if not r.exists(user_events):
            evs = []
        else:
            evs = json.loads(r.get(user_events))

        new_ev = {
            "id": int(max((x['id'] for x in evs)))+1 if evs else 1,
            "date": date,
            "time": time,
            "text": text,
        }
        evs.append(new_ev)

        r.set(user_events, json.dumps(evs))
        WEBSOCKETS['user_ws:{0}'.format(user_id)].write_message(
            json.dumps(new_ev))


class EditEventHandler(BaseHandler):

    def get(self):
        ev_id = int(self.get_argument('eventId'))
        user_events = 'user_events:{0}'.format(self.user_id)
        evs = json.loads(r.get(user_events))
        ev = filter(lambda x: x["id"] == ev_id, evs)[0]
        self.write(json.dumps(ev))

    def post(self):
        ev_id = int(self.get_argument('eventId'))

        user_events = 'user_events:{0}'.format(self.user_id)
        evs = json.loads(r.get(user_events))
        ev = filter(lambda x: x["id"] == ev_id, evs)[0]

        ev["date"] = self.get_argument('eventDate')
        ev["time"] = self.get_argument('eventTime')
        ev["text"] = self.get_argument('eventText')

        r.set(user_events, json.dumps(evs))

        self.finish()

class GetEventsHandler(BaseHandler):

    def get(self):
        user_events = 'user_events:{0}'.format(self.user_id)
        if not r.exists(user_events):
            self.write('[]')
        else:
            self.write(r.get(user_events))


# list of all websockets
WEBSOCKETS = {}


class SocketHandler(WebSocketHandler):

    @property
    def user_id(self):
        return self.get_cookie("tornado_user_id")

    def open(self):
        WEBSOCKETS['user_ws:{0}'.format(self.user_id)] = self

    def on_message(self, message):
        self.write_message(u"You said: " + message)

    def on_close(self):
        del WEBSOCKETS['user_ws:{0}'.format(self.user_id)]


class LogoutHandler(BaseHandler):

    def get(self):
        self.clear_cookie("tornado_user_id")

        self.redirect('/')


__CURRENT_DIR__ = os.path.dirname(os.path.abspath(__file__))


class FileUploadHandler(BaseHandler):

    def post(self):
        file = self.request.files["file"][0]

        fname = file['filename']
        extn = os.path.splitext(fname)[1]
        cname = os.path.join('static', 'uploads', str(uuid.uuid4()) + extn)

        with open(os.path.join(__CURRENT_DIR__, cname), 'w')as fh:
            fh.write(file['body'])

        user_profile = Dict(
            key='user_profile:{0}'.format(self.user_id),
            redis=r
        )
        user_profile["photo"] = cname

        self.write(json.dumps(cname))


settings = dict(
    cookie_secret="43osdETzKXasdQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
    template_path=os.path.join(os.path.dirname(__file__), "templates"),
    static_path=os.path.join(os.path.dirname(__file__), "static"),
)

application = Application([
    (r"/", MainHandler),
    (r"/login", LoginHandler),
    (r"/registration", RegHandler),
    (r"/get-cities", GetCitiesView),
    (r"/get-profile", GetProfileView),
    (r"/socket", SocketHandler),
    (r"/add-event", NewEventHandler),
    (r"/edit-event", EditEventHandler),
    (r"/get-events", GetEventsHandler),
    (r"/logout", LogoutHandler),
    (r"/file", FileUploadHandler),


], **settings)


if __name__ == "__main__":
    application.listen(8888)
    ioloop.IOLoop.instance().start()
