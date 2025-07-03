from __future__ import annotations

import bisect
from copy import copy
from dataclasses import dataclass, field

from . import LoadGeneratorBase
from ...core import *
from typing import List, Tuple

from ...utils import inject_context, remove_m, shallow_asdict, default_if_none, not_none


def preprocess_rps_list(rps_list):
    rps_list = [(remove_m(x[0]), x[1], 'linear' if len(x) <= 2 else x[2]) for x in rps_list]
    rps_list.sort(key=lambda x: x[0])
    if rps_list[0][0] != 0:
        rps_list.insert(0, (0, 0, 'linear'))
    return rps_list


@dataclass
class DynamicRPSLoadGeneratorConfig(Config):
    rps_list: List[Tuple[float | str, float, str]]
    host: str
    endpoint: str
    request_config: Config = None
    timeout: int | str = None
    name: str = None
    network_group: str = None
    by_proxy: bool = None

    def generator(self):
        d = shallow_asdict(self)
        request_config = d.pop('request_config', None)
        d['request_gen'] = None if request_config is None else request_config.generator()
        return lambda ctx, proxy=None: DynamicRPSLoadGenerator(ctx, proxy, **d)

    @classmethod
    def from_json(cls, j, builder):
        j = copy(j)
        j['request_config'] = builder.use_config(j.get('request_config'))
        return cls(**j)


class DynamicRPSLoadGenerator(LoadGeneratorBase):
    def __init__(self, context: Context, proxy, rps_list, host, endpoint, request_gen=None, timeout=None, name=None,
                 network_group=None, by_proxy=None):
        super().__init__(context, proxy, name=name, network_group=network_group)
        self.client = Client(context, owner=self)
        self.timeout_v = timeout # can be none
        self.rps_list = preprocess_rps_list(not_none(rps_list))
        self.host = not_none(host)
        self.endpoint = not_none(endpoint)
        self.request_gen = default_if_none(request_gen, MessageConfig().generator())
        self.by_proxy = default_if_none(by_proxy, False)
        self.run(self.process())

    def rps(self, t):
        times = [x[0] for x in self.rps_list]
        idx = bisect.bisect_left(times, t)

        if idx == 0:
            start_time, start_value, _ = self.rps_list[0]
            end_time, end_value, mode = self.rps_list[1]
        elif idx == len(self.rps_list):
            start_time, start_value, _ = self.rps_list[-2]
            end_time, end_value, mode = self.rps_list[-1]
        else:
            start_time, start_value, _ = self.rps_list[idx - 1]
            end_time, end_value, mode = self.rps_list[idx]

        if start_time <= t < end_time:
            if mode == 'linear':
                return start_value + (end_value - start_value) * (t - start_time) / (end_time - start_time)
            elif mode == 'step_start':
                return end_value
            elif mode == 'step_end':
                return start_value
            elif mode == 'accelerating':
                return start_value + (end_value - start_value) * ((t - start_time) / (end_time - start_time)) ** 2
            elif mode == 'decelerating':
                return start_value + (end_value - start_value) * (
                        1 - (1 - (t - start_time) / (end_time - start_time)) ** 2)
        return self.rps_list[-1][1]

    def process(self):
        while True:
            if self.rps(self.now()) >= 1:
                yield self.timeout(1 / self.rps(self.now()))
                p = self.client.send_request(self.host, self.endpoint, inject_context(self.request_gen, self.context),
                                             timeout=self.timeout_v,
                                             proxy=self.proxy,
                                             by_proxy=self.by_proxy)
            else:
                yield self.timeout(0.1)
