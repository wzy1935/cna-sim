from . import *


class Promise(Base):
    def __init__(self, context):
        super().__init__(context)
        self.response = None
        self.error = None
        self.failed = False
        self.succeed = False
        self.alive = self.context.env.event()

    @staticmethod
    def init(context, gen):
        p = Promise(context)

        def _(gen, context=context, p=p):
            try:
                resp = yield context.run(gen)
                p.resolve(resp)
            except (SimException, SimError) as e:
                p.reject(e)

        context.run(_(gen))
        return p

    def reject(self, error):
        if self.failed or self.succeed:
            return
        self.failed = True
        self.error = error
        self.alive.succeed()

    def resolve(self, response):
        if self.failed or self.succeed:
            return
        self.succeed = True
        self.response = response
        self.alive.succeed()

    def then(self, callback):
        p = Promise(self.context)

        def _(p, callback):
            yield self.alive
            if self.succeed:
                p.request = self.response
                try:
                    res = yield self.run(callback(self.response))
                    p.resolve(res)
                except (SimException, SimError) as e:
                    p.reject(e)
            else:
                p.reject(self.error)

        self.run(_(p, callback))
        return p

    def catch(self, callback):
        p = Promise(self.context)

        def _(p, callback):
            yield self.alive
            if self.failed:
                try:
                    res = yield self.run(callback(self.error))
                    p.resolve(res)
                except (SimException, SimError) as e:
                    p.reject(e)
            else:
                p.resolve(self.response)

        self.run(_(p, callback))
        return p

    def wait(self):
        def _():
            yield self.alive
            if self.succeed:
                return self.response
            else:
                raise self.error

        return self.run(_())

    @staticmethod
    def race(context, promises):
        def _(context, promises):
            events = [x.wait() for x in promises]
            try:
                resp = yield context.env.any_of(events)
            except Exception as e:
                for ev in events:
                    ev.defused = True # silence other potential exceptions before this being operated
                raise e

            for e in events:
                e.defused = True # silence other potential exceptions
            return list(resp.values())[0]

        return Promise.init(context, _(context, promises))
