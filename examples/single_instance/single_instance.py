from cna_sim.components.data_collectors import DefaultDataCollector
from cna_sim.components.endpoints import StaticEndPoint
from cna_sim.components.instances import SyncServerConfig
from cna_sim.components.load_generators import RPSLoadGeneratorConfig
from cna_sim.core import RequestContext, Context, ContextConfig, Config
from cna_sim.utils import Distribution

"""
The simulation includes:

- A server instance with an endpoint `/endpoint`, where the response time of 0.1s.
- A load generator that sends 2 requests per second to the `/endpoint` of the service instance.
- A custom data collector that records and prints the request's sent time and the response arrival time.

The simulation runs for a duration of 3 seconds.
"""


class PrintDataCollector(DefaultDataCollector):
    def record_ended_request(self, rc: RequestContext):
        print(f'instance: {rc.instance_name}\t endpoint: {rc.endpoint_name}\t'
              f'sent at {rc.req_sent:.2f}\t recv at: {rc.resp_arrived:.2f}\t status: {rc.status}')


context = ContextConfig(
    data_collector_config=Config.of(lambda ctx: PrintDataCollector(ctx))
).generate()
context.gateway.register_hosts(['my_instance'])

endpoint_config = Config.of(
    lambda ctx, ins: StaticEndPoint(ctx, ins).add('/endpoint', [], Distribution(mean=0.1)))

SyncServerConfig(
    endpoint_config=endpoint_config,
    cpu_quota=4,
    queue_size=200,
    threads=8,
    name='my_instance'
).generate(context)

RPSLoadGeneratorConfig(
    rps=2,
    host='my_instance',
    endpoint='/endpoint'
).generate(context)

context.simulate(until=3)
context.close()
