from ...core import *


class NetworkBase(Base):
    def __init__(self, context: Context, name=None):
        super().__init__(context, name, in_context=True)

    def transmit(self, message: Message, comp_sent: Agent, comp_recv: Agent):
        raise NotImplementedError()


