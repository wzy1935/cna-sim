from copy import copy
from dataclasses import dataclass

from ...core import *
from .autoscaler_base import AutoScalerBase

@dataclass
class DefaultScalerConfig(Config):
    name: str = None

    def generator(self):
        return lambda ctx, svc: DefaultScaler(ctx, self.name)


class DefaultScaler(AutoScalerBase):
    def __init__(self, context: Context, name=None):
        super().__init__(context, name)
