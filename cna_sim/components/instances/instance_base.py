from __future__ import annotations
from ...core import *
from ...utils import Distribution


class InstanceBase(Agent):
    def __init__(self, context: Context, name=None, service_name=None, network_group='default'):
        self.service_name = service_name
        super().__init__(context, name, network_group)

    def compute(self, cpu_time: Distribution):
        raise NotImplementedError()

    def send_request(self, host, endpoint, request, timeout=0):
        raise NotImplementedError()

    def terminate(self):
        pass





