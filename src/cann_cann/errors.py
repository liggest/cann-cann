"""Exceptions raised by :mod:`cann_cann`."""


class CannCannError(Exception):
    """Base class for all public cann-cann errors."""


class CANNNotFoundError(CannCannError):
    """Raised when a usable CANN installation cannot be found."""


class NPUDetectionError(CannCannError):
    """Raised when the current NPU name cannot be detected."""


class PlatformConfigError(CannCannError):
    """Raised when a CANN platform configuration cannot be used."""


class PlatformConfigNotFoundError(PlatformConfigError, FileNotFoundError):
    """Raised when a requested platform configuration file cannot be found."""
