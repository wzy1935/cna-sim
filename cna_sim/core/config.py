from copy import copy

class Config:
    def generator(self):
        raise NotImplementedError()

    def generate(self, *args):
        return self.generator()(*args)

    @classmethod
    def of(cls, generator):
        config = Config()
        def config_generator():
            return generator
        config.generator = config_generator
        return config

    @classmethod
    def from_json(cls, j, builder):
        j = copy(j)
        return cls(**j)

    @classmethod
    def kind(cls):
        return cls.__name__

