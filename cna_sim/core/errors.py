class SimException(Exception):
    def __init__(self, code, data=None):
        self.code = code
        self.data = data

    def __str__(self):
        return f'{self.code}, {self.data}'


class SimError(Exception):
    def __init__(self, code, data=None):
        self.code = code
        self.data = data

    def __str__(self):
        return f'{self.code}, {self.data}'

