from cna_sim.components.endpoints import sync_api, DefaultEndPoint
from cna_sim.components.instances import SyncServer, SyncServerConfig
from cna_sim.components.proxies import Gateway, GatewayConfig
from cna_sim.core import Message, ContextConfig, Config, Client
from cna_sim.utils import Distribution


"""
The simulation includes:

- An instance with two endpoints: `/add` and `/sub`, performing addition and subtraction.
- A client that sends requests to the service instance and waits for the responses.
- A custom gateway that proxies requests from the client to the service instance.

The simulation runs for 3 seconds.
"""

context = ContextConfig().generate()


class MyEndPoint(DefaultEndPoint):
    @sync_api('/add')
    def add(self, request):
        print(f'Received request {request} at {context.now():.2f}s.')
        yield self.instance.compute(Distribution(mean=0.1))
        a = request.attachment['a']
        b = request.attachment['b']
        return Message({'c': a + b})

    @sync_api('/sub')
    def sub(self, request):
        print(f'Received request {request} at {context.now():.2f}s.')
        yield self.instance.compute(Distribution(mean=0.1))
        a = request.attachment['a']
        b = request.attachment['b']
        return Message({'c': a - b})


SyncServerConfig(
    endpoint_config=Config.of(lambda ctx, ins: MyEndPoint(ctx, ins)),
    threads=16,
    cpu_quota=1,
    queue_size=200,
    name='my_instance'
).generate(context)

custom_gateway = GatewayConfig().generate(context)
custom_gateway.register_hosts(['my_instance'])

client = Client(context)


def run():
    resp = yield client.send_request(
        host='my_instance',
        endpoint='/add',
        request=Message({'a': 1, 'b': 2}),
        proxy=custom_gateway
    ).wait()
    print(f'Received response {resp} at {context.now():.2f}s.')

    resp = yield client.send_request(
        host='my_instance',
        endpoint='/sub',
        request=Message({'a': 1, 'b': 2}),
        proxy=custom_gateway
    ).wait()
    print(f'Received response {resp} at {context.now():.2f}s.')


context.run(run())
context.simulate(until=3)
context.close()
