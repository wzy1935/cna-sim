from __future__ import annotations

from copy import copy
from dataclasses import dataclass
from typing import List, Tuple

from .default_endpoint import DefaultEndPoint
from ...core import *
from ...utils import Distribution


@dataclass
class StaticEndPointConfig(Config):
    endpoints: List[
        Tuple[str, List[Tuple[str, str]], any]
    ]

    def generator(self):
        def endpoint_gen(ctx, ins):
            endpoint = StaticEndPoint(ctx, ins)
            for e in self.endpoints:
                endpoint.add(*e)
            return endpoint
        return endpoint_gen

    @classmethod
    def from_json(cls, j, builder):
        j = copy(j)
        """ example
        j = [{
            "endpoint_name": "/xxx",
            "dependencies": [['A', '/aaa'], ['B', '/bbb']]
            "computation_time": {
                "mean": 1,
                "std": 0.5,
                "dis": "lognormal"
            }
        }, ...]
        """
        return cls(endpoints=[(x['endpoint_name'], x['dependencies'], Distribution.from_json(x['computation_time'])) for x in j])

class StaticEndPoint(DefaultEndPoint):
    def __init__(self, context: Context, instance):
        super().__init__(context, instance)

    def add(self, endpoint_name, dependencies, computation_time) -> StaticEndPoint:
        def api(request, endpoint_name=endpoint_name, dependencies=dependencies, computation_time=computation_time):
            yield self.instance.compute(computation_time)
            for host, endpoint in dependencies:
                yield self.instance.send_request(host, endpoint, Message()).wait()
            return Message()
        self.endpoints[endpoint_name] = api
        return self