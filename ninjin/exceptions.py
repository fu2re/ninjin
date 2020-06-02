class ImproperlyConfigured(Exception):
    pass


class UnknownConsumer(Exception):
    pass


class UnknownHandler(Exception):
    pass


class IncorrectMessage(Exception):
    pass


class ValidationError(Exception):
    pass
