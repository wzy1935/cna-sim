from __future__ import annotations

from . import *


class Client(Agent):
    def __init__(self, context: Context, name=None, network_group='default', in_context=True, owner: Agent=None):
        super().__init__(context, name, network_group, in_context=in_context)
        if owner is None:
            owner = self
        self.owner = owner

    def send_request(self, host: str, endpoint: str, request: Message, timeout: float=None, proxy=None, by_proxy=False) -> Promise:
        if proxy is None:
            proxy = self.context.gateway
        rc = RequestContext(self.context, request)
        rc.req_sent = self.now()
        if by_proxy:
            receiver = proxy
            rc.instance_name = proxy.name
        else:
            receiver = proxy.find_component(host, endpoint, rc)
            rc.host_name = host
            rc.endpoint_name = endpoint

        def send_delay(rc=rc, sender=self.owner, receiver=receiver, host=host, endpoint=endpoint):
            try:
                yield self.run(self.context.network.transmit(rc.request, sender, receiver))
            except SimException as e:
                rc.failed_at = self.now()
                rc.status = e.code
                raise e
            receiver.recv_request(host, endpoint, rc)
            return None

        def recv_delay(resp, rc=rc, sender=receiver, receiver=self.owner):
            try:
                yield self.run(self.context.network.transmit(resp, sender, receiver))
            except SimException as e:
                rc.failed_at = self.now()
                rc.status = e.code
                raise e
            rc.resp_arrived = self.now()
            return resp

        resp_promise = (Promise.init(self.context, None)
                        .then(lambda _: (yield self.run(send_delay())))
                        .then(lambda _: (yield rc.server_promise.wait()))
                        .then(lambda resp: (yield self.run(recv_delay(resp)))))
        resp_promise.then(lambda _, rc=rc: self.context.data_collector.record_ended_request(rc))
        resp_promise.catch(lambda _, rc=rc: self.context.data_collector.record_ended_request(rc))

        if timeout is None:
            return resp_promise

        timeout_promise = Promise(self.context)
        def _timeout(timeout, rc=rc, timeout_promise=timeout_promise):
            yield self.timeout(timeout)
            rc.is_timeout = True
            timeout_promise.reject(SimException('TIMEOUT'))

        self.run(_timeout(timeout))

        return Promise.race(self.context, [resp_promise, timeout_promise])

