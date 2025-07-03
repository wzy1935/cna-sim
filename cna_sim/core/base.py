from .context import Context
from .. import utils


class Base:
    def __init__(self, context: Context, name=None, in_context=False):
        self.context = context
        if name is None:
            name = utils.uuid()
        self.name = name
        if in_context:
            self.context.components[name] = self

    def run(self, generator, delay=0):
        return self.context.run(generator, delay)

    def alive_race(self, generator, alive_event, generator_error=None, alive_error=None):
        return self.context.alive_race(generator, alive_event, generator_error, alive_error)

    def timeout(self, t):
        return self.context.timeout(t)

    def now(self):
        return self.context.now()


class Agent(Base):
    def __init__(self, context: Context, name=None, network_group='default', in_context=True):
        super().__init__(context, name, in_context)
        self.network_group = network_group

    def metric(self, name):
        pass

    def recv_request(self, host, endpoint, request_context):
        raise NotImplementedError()