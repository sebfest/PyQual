class InputError(Exception):
    """Is raised when an input if wrong."""
    pass


class MissingApiTokenError(Exception):
    """Is raised when qualtrics api key is missing."""
    pass


class InvalidDataCenterError(Exception):
    """Is raised when qualtrics datacenter is wrong."""
    pass


class ExportFailureError(Exception):
    """Is raised when export is aborted."""
    pass
