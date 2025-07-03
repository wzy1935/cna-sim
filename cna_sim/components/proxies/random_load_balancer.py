from ...core import *
from .proxy_base import ProxyBase
from dataclasses import dataclass
import random

from ...utils import shallow_asdict


@dataclass
class RandomLoadBalancerConfig(Config):
    name: str = None

    def generator(self):
        return lambda ctx, svc: RandomLoadBalancer(ctx, svc, **shallow_asdict(self))


class RandomLoadBalancer(ProxyBase):
    def __init__(self, context, service, name=None):
        super().__init__(context, name)
        self.service = service

    def find_component(self, host: str, name: str=None, request: RequestContext=None):
        x = [y for y in list(self.service.instances.values()) if y.metric('status') == 'ACTIVE']
        if len(x) == 0:
            return None
        x = random.choice(x)
        return x