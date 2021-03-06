class OmrException(Exception):
    pass


class OmrValidationException(OmrException):
    pass


class ZeroCodeFoundException(OmrException):
    pass


class EmptyFolderException(FileNotFoundError):
    pass


class AbortException(OmrException):
    pass


class CircleParseError(Exception):
    pass
