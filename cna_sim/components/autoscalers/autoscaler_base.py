from ...core import *

class AutoScalerBase(Base):
    def __init__(self, context: Context, name=None, in_context=True):
        super().__init__(context, name, in_context)