class DomainException(Exception):
    """Base exception for domain errors"""
    pass

class UserNotFoundError(DomainException):
    """Raised when a user is not found"""
    pass

class UserAlreadyExistsError(DomainException):
    """Raised when trying to create a user that already exists"""
    pass

class DatabaseError(DomainException):
    """Raised when a database operation fails"""
    pass

class InvalidPasswordError(DomainException):
    """Raised when password verification fails"""
    pass

class TokenExpiredError(DomainException):
    """Raised when a token has expired"""
    pass

class InvalidTokenError(DomainException):
    """Raised when a token is invalid"""
    pass