from __future__ import annotations

from dataclasses import is_dataclass, fields

import numpy as np
from uuid import uuid4
from types import GeneratorType, FunctionType


def default_if_none(value, default):
    return default if value is None else value


def not_none(value):
    assert value is not None
    return value


def remove_m(v):
    if v is None:
        return None
    if type(v) is str and v[-1] == 'm':
        return float(v[:-1]) / 1000
    return float(v)


def to_timestamp_ns(dt):
    if dt is None:
        return None
    return int(dt.timestamp() * 1_000_000_000)


def inject_context(gen, *args):
    if type(gen) is FunctionType:
        return gen(*args)
    else:
        return gen


def uuid():
    return str(uuid4())


def shallow_asdict(obj):
    if not is_dataclass(obj):
        raise TypeError("Expected dataclass instance")
    return {f.name: getattr(obj, f.name) for f in fields(obj)}


def fit_lognormal(mean, std):
    if mean <= 0 or std < 0:
        raise ValueError(f"Mean {mean} and std {std} must be positive.")
    variance = std ** 2
    sigma_squared = np.log(1 + variance / mean ** 2)
    sigma = np.sqrt(sigma_squared)

    mu = np.log(mean) - 0.5 * sigma_squared
    return np.random.lognormal(mean=mu, sigma=sigma)


class Distribution:
    def __init__(self, mean: float | str = 0, std: float | str = 0, dis: str = 'lognormal'):
        self.mean = remove_m(mean)
        self.std = remove_m(std)
        self.dis = dis

    @staticmethod
    def from_json(j):
        return Distribution(**j)

    def sample(self):
        if self.dis == 'lognormal':
            return fit_lognormal(self.mean, self.std)
        elif self.dis == 'normal':
            return np.random.normal(loc=self.mean, scale=self.std)
        else:
            return NotImplementedError()
