from copy import copy
from dataclasses import dataclass, field
from typing import List

from .proxy_base import ProxyBase
from ...core import *
from ...utils import default_if_none, shallow_asdict


@dataclass
class GatewayConfig(Config):
    components: List[str] = None
    name: str = None
    network_group: str = None

    def generator(self):
        return lambda ctx: Gateway(ctx, **shallow_asdict(self))


class Gateway(ProxyBase):
    def __init__(self, context, components=None, name=None, network_group=None):
        super().__init__(context, name=name, network_group=network_group)
        self.components = set(default_if_none(components, []))
        self.client = Client(context, owner=self)

    def register_hosts(self, components: List[str]):
        self.components |= set(components)

    def find_component(self, host: str, name: str=None, request: RequestContext=None):
        assert host in self.components
        return self.context.components[host]

    def recv_request(self, host, endpoint, request_context: RequestContext):
        def _(host, endpoint, rc):
            rc.req_arrived = self.now()
            rc.proc_started = self.now()
            try:
                resp = yield self.client.send_request(host, endpoint, request_context.request).wait()
                rc.proc_success(resp)
            except SimException as e:
                rc.fail(SimException('SERVER_ERROR'), True)
        self.run(_(host, endpoint, request_context))
