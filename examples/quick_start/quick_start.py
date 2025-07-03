from cna_sim.components.endpoints import StaticEndPoint
from cna_sim.components.instances import SyncServerConfig
from cna_sim.components.load_generators import RPSLoadGenerator
from cna_sim.components.services import ServiceConfig
from cna_sim.core import ContextConfig, Config
from cna_sim.utils import Distribution
import logging


logging.basicConfig(level=logging.INFO)

context = ContextConfig().generate()

load_generator = RPSLoadGenerator(
    context,
    proxy=context.gateway,
    rps=10,
    host='my_service',
    endpoint='/my_endpoint'
)

ServiceConfig(
    SyncServerConfig(
        Config.of(lambda ctx, inst: StaticEndPoint(ctx, inst).add('/my_endpoint', [], Distribution(mean=0.06)))
    ),
    name='my_service'
).generate(context)
context.gateway.register_hosts(['my_service'])

def change_rps():
    yield context.timeout(10)
    load_generator.rps = 20
context.run(change_rps())

context.simulate(until=30)
context.close()