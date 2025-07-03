from ...core import *

class ProxyBase(Agent):
    def __init__(self, context, name=None, network_group='default'):
        super().__init__(context, name, network_group)

    def find_component(self, host: str, name: str=None, request: RequestContext=None):
        raise NotImplementedError()

    def recv_request(self, host, endpoint, request_context: RequestContext):
        raise NotImplementedError()