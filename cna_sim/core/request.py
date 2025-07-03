from dataclasses import dataclass

from . import Config
from .base import Base
from .promise import Promise


@dataclass
class MessageConfig(Config):
    attachment: any = None
    size: int = 0

    def generator(self):
        return lambda ctx: Message(self.attachment, self.size)


class Message:
    def __init__(self, attachment=None, size=0):
        self.attachment = attachment
        self.size = size

    def __str__(self):
        return f'Msg({self.attachment})'


class RequestContext(Base):
    def __init__(self, context, request):
        super().__init__(context)
        self.request = request
        self.response = None
        self.host_name = None
        self.endpoint_name = None
        self.instance_name = None
        self.status = None

        self.req_sent = None
        self.req_arrived = None
        self.proc_started = None
        self.proc_completed = None
        self.resp_arrived = None
        self.failed_at = None
        self.is_timeout = False
        self.mark = True

        self.server_promise = Promise(context)

    def fail(self, error, at_server=False):
        self.failed_at = self.now()
        self.status = error.code
        if at_server:
            self.server_promise.reject(error)

    def proc_success(self, resp):
        self.proc_completed = self.now()
        self.status = 'SUCCEED'
        self.response = resp
        self.server_promise.resolve(resp)


