import logging
import os.path
import uuid
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
    
class EchoWebSocket(tornado.websocket.WebSocketHandler):    
    def check_origin(self, origin):
        return True
    def open(self):
        self.write_message('Welcome to WebSocket')
        print("WebSocket opened")

    def on_message(self, message):
        self.write_message(u"You said: " + message)

    def on_close(self):
        print("WebSocket closed")

def main():
    app = tornado.web.Application([
        (r"/setpage", SetPageHandler)
    ])
    app.listen(8888)
    tornado.ioloop.IOLoop.instance().start()    
if __name__ == '__main__':
    main()