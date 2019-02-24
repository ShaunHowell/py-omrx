class OmrException(Exception):
    pass


class OmrValidationException(OmrException):
    pass


class ZeroCodeFoundException(OmrException):
    pass
