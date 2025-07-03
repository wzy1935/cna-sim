from ...core import *


class LoadGeneratorBase(Agent):
    def __init__(self, context: Context, proxy=None, name=None, network_group='default'):
        super().__init__(context, name=name, network_group=network_group)
        if proxy is None:
            proxy = self.context.gateway
        self.proxy = proxy
