import math
from dataclasses import dataclass, asdict
from copy import copy

from ...utils import remove_m, not_none, default_if_none, shallow_asdict
from .autoscaler_base import AutoScalerBase
from ...core import *


@dataclass
class HorizontalAutoscalerConfig(Config):
    metric_name: str
    target_value: float
    enabled: bool = None
    min_num: int = None
    max_num: int = None
    interval: float = None
    downscale_stabilization_window: float = None
    name: str = None

    def generator(self):
        return lambda ctx, svc: HorizontalAutoscaler(
            ctx, svc, **shallow_asdict(self))

    @classmethod
    def from_json(cls, j, builder):
        j = copy(j)
        j['interval'] = remove_m(j.get('interval'))
        j['downscale_stabilization_window'] = remove_m(j.get('downscale_stabilization_window'))
        return cls(**j)


class HorizontalAutoscaler(AutoScalerBase):
    def __init__(self, context: Context, service, metric_name, target_value, enabled=None, min_num=None, max_num=None,
                 interval=None,
                 downscale_stabilization_window=None, name=None):
        super().__init__(context, name)
        self.service = not_none(service)
        self.enabled = default_if_none(enabled, True)
        self.min_num = default_if_none(min_num, 1)
        self.max_num = default_if_none(max_num, 10)
        self.interval = default_if_none(interval, 15)
        self.metric_name = not_none(metric_name)
        self.target_value = not_none(target_value)
        self.downscale_stabilization_window = default_if_none(downscale_stabilization_window, 300)

        self._last_trigger = 0
        self._stable_window = []

        self.run(self.process())

    @staticmethod
    def scale_compute(current_replica, target_util, current_util, min_v, max_v):
        optimal = math.ceil(current_replica * current_util / target_util)
        optimal = max(min_v, optimal)
        optimal = min(max_v, optimal)
        return optimal

    def scale(self):
        metric_list = [x.metric(self.metric_name) for x in self.service.instances.values() if
                       x.metric('status') == 'ACTIVE']
        if len(metric_list) == 0:
            return
        avg_metric = sum(metric_list) / len(metric_list)
        self._stable_window.append((self.now(), avg_metric))
        self._stable_window = [x for x in self._stable_window if
                               x[0] > self.now() - self.downscale_stabilization_window]
        current_replica = len(metric_list)
        window_avg_metric = max([avg_metric, *[x[1] for x in self._stable_window]])
        optimal = HorizontalAutoscaler.scale_compute(current_replica, self.target_value, avg_metric, self.min_num,
                                                     self.max_num)
        window_optimal = HorizontalAutoscaler.scale_compute(current_replica, self.target_value, window_avg_metric,
                                                            self.min_num, self.max_num)

        if optimal >= current_replica:
            self.service.scale_to(optimal)
        elif window_optimal < current_replica:
            self.service.scale_to(window_optimal)

    def process(self):
        while True:
            yield self.timeout(1)
            if not self.enabled:
                continue
            if self.now() - self._last_trigger >= self.interval:
                self._last_trigger += self.interval
                self.scale()
