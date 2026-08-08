"""Exceptions raised by :mod:`cann_cann`."""


class CannCannError(Exception):
    """Base class for all public cann-cann errors."""


class CANNNotFoundError(CannCannError):
    """Raised when a usable CANN installation cannot be found."""


class PlatformConfigNotFoundError(CannCannError):
    """Raised when a requested platform configuration cannot be found."""


class PlatformConfigParseError(CannCannError, ValueError):
    """Raised when a platform configuration cannot be parsed."""


class NPUDetectionError(CannCannError):
    """Raised when the current NPU name cannot be detected."""


class UnsupportedArchitectureError(CannCannError):
    """Raised when the host architecture is unsupported by CANN."""


class ConfigFieldUnavailableError(CannCannError):
    """Raised when a required field is absent from a platform configuration."""


class InvalidUnitError(CannCannError, ValueError):
    """Raised when a size unit is not supported."""
