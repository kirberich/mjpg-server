from twisted.web import http
from twisted.web.http import HTTPChannel
from twisted.internet import reactor, defer
import threading

from settings import LIMIT_FPS

class BotHandler(http.Request, object):
    BOUNDARY = "jpgboundary"

    def get_frame(self):
        return self.api.recorder.frame

    def writeBoundary(self):
        self.write("--%s\n" % (self.BOUNDARY))

    def writeStop(self):
        self.write("--%s--\n" % (self.BOUNDARY))

    def __init__(self, api, *args, **kwargs):
        self.api = api
        self.frame_delay = 1.0/LIMIT_FPS if LIMIT_FPS else 0.05
        super(BotHandler, self).__init__(*args, **kwargs)

    def render(self, content, headers):
        for (header_name, header_value) in headers:
            self.setHeader(header_name, header_value)
        self.write(content)
        self.finish()

    def simple_render(self, content, content_type="text/plain"):
        self.render(content, [("Content-Type", content_type)])

    def not_found(self, message=None):
        self.setResponseCode(404, message)
        return self.simple_render("no no...")

    def wait(self, seconds, result=None):
        """Returns a deferred that will be fired later"""
        d = defer.Deferred()
        reactor.callLater(seconds, d.callback, result)
        return d

    @defer.inlineCallbacks
    def serve_stream(self):
        """ Serve video stream as multi-part jpg. """
        boundary = "jpgboundary"

        self.setHeader('Connection', 'Keep-Alive')
        self.setHeader('Content-Type', "multipart/x-mixed-replace;boundary=%s" % boundary)

        while True:
            if not self.transport._isSendBufferFull():
                content = self.get_frame()
                self.write("Content-Type: image/jpg\n")
                self.write("Content-Length: %s\n\n" % (len(content)))
                self.write(content)
                self.write("--%s\n" % (boundary))

            if self.transport.disconnected:
                break

            yield self.wait(self.frame_delay)

    def serve_stream_container(self):
        headers = [("content-type", "text/html")]

        url = '/stream.avi'
        if 'pwd' in self.args:
            url += '?pwd={}'.format(self.args['pwd'][0])

        content = "<html><head><title>MJPG Server</title></head><body><img src='{}' alt='stream'/></body></html>".format(url)
        self.render(content, headers)

    def serve_frame(self):
        return self.simple_render(self.get_frame(), "image/jpg")

    def process(self):
        command_args_list = [x for x in self.path.split("/") if x]
        command = ""
        args = []
        if command_args_list:
            command = command_args_list[0]
            args = command_args_list[1:]

        if PASSWORD:
            if 'pwd' not in self.args or self.args['pwd'][0].split("?")[0] != PASSWORD:
                self.setResponseCode(403)
                return self.simple_render("Password required")

        try:
            if command.startswith("stream"):
                return self.serve_stream()
            elif command == "snapshot":
                return self.serve_frame()
            else:
                return self.serve_stream_container()
        except Exception, e:
            return self.simple_render(e.message)

        return self.not_found()


class BotHandlerFactory(object):
    def __init__(self, api):
        self.api = api

    def __call__(self, *args, **kwargs):
        return BotHandler(self.api, *args, **kwargs)


class StreamFactory(http.HTTPFactory):
    protocol = HTTPChannel


class Api(object):
    def __init__(self, recorder):
        # This I believe is what you find when you look up "ugly" in the dictionary
        # But I really don't want to try and understand this FactoryFactoryFactory stuff properly
        HTTPChannel.requestFactory = BotHandlerFactory(api=self)

        self.recorder = recorder
        self.events = []
        self.lock = threading.Lock()

    def demonize(self, port=8080):
        reactor.listenTCP(port, StreamFactory())
        t = threading.Thread(target=reactor.run)
        t.daemon = True
        t.start()

    def run(self, port=8080):
        reactor.listenTCP(port, StreamFactory())
        reactor.run()
