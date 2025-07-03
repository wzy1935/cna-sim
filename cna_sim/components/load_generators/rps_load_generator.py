from copy import copy
from dataclasses import dataclass, field

from ...core import *
from .load_generator_base import LoadGeneratorBase
from ...utils import inject_context, default_if_none, not_none, shallow_asdict


@dataclass
class RPSLoadGeneratorConfig(Config):
    rps: int
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
        return lambda ctx, proxy=None: RPSLoadGenerator(ctx, proxy, **d)

    @classmethod
    def from_json(cls, j, builder):
        j = copy(j)
        if j.get('request_config') is not None:
            j['request_config'] = builder.use_config(j.get('request_config'))
        return cls(**j)


class RPSLoadGenerator(LoadGeneratorBase):
    def __init__(self, context: Context, proxy, rps, host, endpoint, request_gen=None, timeout=None, name=None,
                 network_group=None, by_proxy=None):
        super().__init__(context, proxy, name, network_group)
        self.client = Client(context, owner=self)
        self.timeout_v = timeout  # can be none
        self.rps = not_none(rps)
        self.host = not_none(host)
        self.endpoint = not_none(endpoint)
        self.request_gen = default_if_none(request_gen, MessageConfig().generator())
        self.by_proxy = default_if_none(by_proxy, False)
        self.run(self.process())

    def process(self):
        while True:
            if self.rps > 0:
                yield self.timeout(1 / self.rps)
                self.client.send_request(self.host, self.endpoint, inject_context(self.request_gen, self.context),
                                         proxy=self.proxy, timeout=self.timeout_v,
                                         by_proxy=self.by_proxy)
            else:
                yield self.timeout(0.1)
