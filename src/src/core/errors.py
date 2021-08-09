class UnexpectedTypeError(Exception):
    """Raised when a variable isn't of a supported type"""
    def __init__(self, expected=None, actual=None, name=None):
        self.__expected = expected
        self.__actual = actual
        self.__name = name or 'variable'

    def __str__(self):
        name = f"'{self.__name}'"
        if self.__actual is not None:
            rv = f'{name} is of type {self.__actual}'
            if self.__expected is not None:
                rv += f' (expected {self.__expected})'
            return rv
        elif self.__expected is not None:
            return f'Expected {name} to be of type {self.__expected}'
        return f"{name} isn't of an expected type"
