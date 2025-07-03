# Message Passing

Messages are passed using the `RequestContext` class, which records the request and response bodies, the request status, timestamps for each status transition, and more. The actual message content is represented by the `Message` class, where you can set the `attachment` and `size` fields to specify the payload and its size, respectively.

You can send a message using the `Client`:

```python
client = Client(context)
client.send_request('service_a', '/endpoint_a', Message('hello', 5))
```

When this method is called, the client creates a `RequestContext` and uses the gateway to locate the appropriate component to handle the request. It then calls that component's `recv_request` method. For example, if the target component is `service_a`, the client essentially performs the following simplified operation on your behalf:

```python
rc = RequestContext(context, Message('hello', 5))
context['service_a'].recv_request('service_a', '/endpoint_a', rc)
```

While you can manually create a `RequestContext` and call `recv_request` to simulate message passing, it's generally not recommended. Doing so requires you to manually manage the full lifecycle of the `RequestContext`, including setting most fields and applying network delays yourself.

The `Client.send_request` method returns a `Promise` object, which you can wait on:

```python
promise = client.send_request(...)
try:
    resp = yield promise.wait()
    print(resp)
except SimException as e:
    print(e)
```

Alternatively, you can attach callbacks:

```python
promise = client.send_request(...)
def if_succeed(resp):
    print(resp)

def if_failed(err):
    print(err)

promise.then(if_succeed).catch(if_failed)
```

Whenever a message completes—whether successfully or due to an error—the `DataCollector`'s `record_ended_request` method is called.
