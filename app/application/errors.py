class ApplicationError(Exception):
    """Base exception for Application Layer errors."""


class EntityNotFound(ApplicationError):
    """Raised when an application entity cannot be found."""


class InvalidOperation(ApplicationError):
    """Raised when an application operation is not valid."""


class ValidationFailure(ApplicationError):
    """Raised when application-level validation fails."""


class UnauthorizedOperation(ApplicationError):
    """Raised when an operation is not authorized."""
