from dataclasses import dataclass

from ...core import *
from .network_base import NetworkBase

@dataclass
class DefaultNetworkConfig(Config):
    name: str = None

    def generator(self):
        return lambda ctx: DefaultNetwork(ctx, self.name)


class DefaultNetwork(NetworkBase):
    def __init__(self, context: Context, name=None):
        super().__init__(context, name=name)

    def transmit(self, message: Message, comp_sent: Agent, comp_recv: Agent):
        return self.timeout(0)