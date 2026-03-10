class AstrologyError(Exception):
    """Domain-level exception for astrology calculation failures."""


class ValidationError(AstrologyError):
    """Raised when user input is not valid for astrology computation."""
