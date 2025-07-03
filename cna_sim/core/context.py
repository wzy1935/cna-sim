from copy import copy
from types import GeneratorType, FunctionType
from typing import List

from . import *
import simpy
from ..utils import inject_context, default_if_none


class ContextConfig(Config):
    def __init__(self, gateway_config: Config = None, data_collector_config: Config = None,
                 network_config: Config = None, component_configs: List[Config]=None):

        self.component_configs = component_configs
        self.gateway_config = gateway_config
        self.data_collector_config = data_collector_config
        self.network_config = network_config

    def generator(self):
        return lambda: Context(
            component_gens=[x.generator() for x in default_if_none(self.component_configs, [])],
            gateway_gen=None if self.gateway_config is None else self.gateway_config.generator(),
            data_collector_gen=None if self.data_collector_config is None else self.data_collector_config.generator(),
            network_gen=None if self.network_config is None else self.network_config.generator()
        )

    @classmethod
    def from_json(cls, j, builder):
        j = copy(j)
        j['component_configs'] = [builder.use_config(x) for x in j['component_configs']]
        j['gateway_config'] = builder.use_config(j.get('gateway_config'))
        j['data_collector_config'] = builder.use_config(j.get('data_collector_config'))
        j['network_config'] = builder.use_config(j.get('network_config'))
        return ContextConfig(**j)


class Context:
    def __init__(self, component_gens=None, gateway_gen=None, data_collector_gen=None, network_gen=None):
        from ..components.data_collectors import DefaultDataCollectorConfig
        from ..components.networks import DefaultNetworkConfig
        from ..components.proxies import GatewayConfig

        self.components = {}
        self.env: simpy.Environment = simpy.Environment()
        self.gateway = default_if_none(gateway_gen, GatewayConfig().generator())(self)
        self.data_collector = default_if_none(data_collector_gen, DefaultDataCollectorConfig().generator())(self)
        self.network = default_if_none(network_gen, DefaultNetworkConfig().generator())(self)
        for component_gen in default_if_none(component_gens, []):
            component_gen(self)

    def __getitem__(self, item):
        return self.components[item]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False

    def run(self, element, delay=0):
        def _():
            yield self.env.timeout(delay)
            if type(element) is GeneratorType:
                return (yield self.env.process(element))
            elif type(element) is FunctionType:
                return element()
            else:
                return element

        return self.env.process(_())

    def alive_race(self, generator, alive_event, generator_error=None, alive_error=None):
        def _(generator, alive_event, generator_error, alive_error):
            if alive_event.triggered:
                if alive_error is not None:
                    raise alive_error
                raise alive_event.value
            try:
                result = yield self.env.any_of([generator, alive_event])
            except (SimException, SimError) as e:
                if generator_error is not None:
                    raise generator_error
                raise e
            k = list(result.keys())[0]
            v = list(result.values())[0]
            if k == alive_event:
                if alive_error is not None:
                    raise alive_error
                raise v
            return v

        return self.env.process(_(generator, alive_event, generator_error, alive_error))

    def timeout(self, t):
        return self.env.timeout(t)

    def now(self):
        return self.env.now

    def simulate(self, until):
        self.env.run(until)
        self.data_collector.flush()

    def close(self):
        self.data_collector.close()
