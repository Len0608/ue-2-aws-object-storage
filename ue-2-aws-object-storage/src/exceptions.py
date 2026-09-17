"""
Exceptions module template for UAC Universal Extensions.

This module provides:
- Base ExecutionError class
- Standard exception types (DataValidationError, ConnectionError, etc.)
- ErrorManager singleton for error collection
- Exit code conventions

CUSTOMIZE:
- Add custom exception types for your extension
- Modify ErrorManager methods if needed
"""
from typing import Optional

class ExecutionError(Exception):
    """
    The default error raised by an extension.

    All extension errors must inherit from it.

    Attrs:
        exit_code: The exit code of the extension (for UAC)
        message: The error message for status description
    """

    exit_code: int = 1
    message: str = "Execution Failed"

    def __init__(self, message: Optional[str] = None):
        """
        Initialize exception.

        Args:
            message: Optional message that will be appended to the default message.

        Note:
            To return result data with errors, use error_manager.set_result()
            before raising the exception.
        """
        if message:
            self.message = f"{self.message}: {message}"

        super().__init__(self.message)

class DataValidationError(ExecutionError):
    """Raised when an input field is invalid."""
    exit_code = 20
    message = "Data Validation Error"

class UnexpectedSystemError(ExecutionError):
    """Raised for unexpected system errors."""
    exit_code = 1
    message = "System Error"

class AWSAuthenticationError(ExecutionError):
    """
    Raised when AWS credential authentication fails.

    Use when boto3 returns a ClientError with code
    InvalidClientTokenId, SignatureDoesNotMatch, or AuthFailure,
    indicating that the Access Key ID or Secret Access Key is invalid.
    """
    exit_code = 1
    message = "Authentication Error: Invalid AWS Access Key ID or Secret Access Key"

class AWSAuthorizationError(ExecutionError):
    """
    Raised when the AWS IAM principal lacks permission to perform an operation.

    Use when boto3 returns a ClientError with code AccessDenied,
    meaning the credentials are valid but the IAM policy denies the
    requested action on the target bucket.
    """
    exit_code = 1
    message = "Authorization Error: Access denied — check IAM permissions for the bucket"

class AWSConfigurationError(ExecutionError):
    """
    Raised when the specified S3 bucket cannot be reached due to a configuration problem.

    Use when boto3 returns a ClientError with code NoSuchBucket,
    meaning the bucket does not exist or is located in a different region
    than the one supplied in the aws_region field.
    """
    exit_code = 1
    message = "Configuration Error: Bucket does not exist or is in a different region"

class AWSValidationError(ExecutionError):
    """
    Raised when user-supplied input fails pre-flight validation before any AWS API call.

    Use when the local file specified by local_file_path does not exist
    on the Universal Agent host filesystem. No AWS call is made in this case.
    """
    exit_code = 20
    message = "Validation Error: Local file not found on the agent host"

class AWSUnexpectedError(ExecutionError):
    """
    Raised for any AWS or network error that does not map to a more specific exception.

    Use when boto3 raises a ClientError whose error code is not covered by
    AWSAuthenticationError, AWSAuthorizationError, or AWSConfigurationError,
    or when any non-ClientError exception occurs (network failure, OS error,
    boto3 internal error).
    """
    exit_code = 1
    message = "Unexpected Error"
