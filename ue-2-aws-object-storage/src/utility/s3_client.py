"""
S3 client utility for the AWS Object Storage Universal Extension.

Manages the boto3 S3 client lifecycle and encapsulates all AWS S3 API
interactions: client initialization, object listing with pagination,
file upload, and ClientError classification into the extension's custom
exception hierarchy.
"""
import logging
from typing import Any

import boto3
from botocore.exceptions import ClientError

from exceptions import (
    ExecutionError,
    AWSAuthenticationError,
    AWSAuthorizationError,
    AWSConfigurationError,
    AWSUnexpectedError,
)

logger = logging.getLogger("UNV")

# Mapping of boto3 ClientError codes to extension exception classes.
_CLIENT_ERROR_MAP: dict[str, type] = {
    "InvalidClientTokenId": AWSAuthenticationError,
    "SignatureDoesNotMatch": AWSAuthenticationError,
    "AuthFailure": AWSAuthenticationError,
    "AccessDenied": AWSAuthorizationError,
    "NoSuchBucket": AWSConfigurationError,
}


def build_s3_client(
    access_key_id: str,
    secret_access_key: str,
    region: str,
) -> Any:
    """
    Create a boto3 S3 client using only explicit credentials.

    Does not fall back to any implicit credential chain (environment
    variables, ~/.aws/credentials, or IAM instance profiles).

    Args:
        access_key_id:     AWS Access Key ID.
        secret_access_key: AWS Secret Access Key.
        region:            AWS region name (e.g. "us-east-1").

    Returns:
        A configured boto3 S3 client instance.
    """
    logger.info("Initializing S3 client for region: %s", region)
    logger.debug(
        "Client parameters: region=%s, access_key_id=%s",
        region,
        "***" if access_key_id else None,
    )
    client = boto3.client(
        "s3",
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        region_name=region,
    )
    logger.info("S3 client initialized")
    return client


def list_objects(
    client: Any,
    bucket_name: str,
    cap: int,
) -> tuple[list[dict[str, Any]], bool]:
    """
    List objects in an S3 bucket with pagination, up to a record cap.

    Iterates through pages using ContinuationToken. Stops when the cap
    is reached or no more pages exist. Sets the truncated flag when the
    cap is reached and the bucket still has additional objects.

    Args:
        client:      A boto3 S3 client (from build_s3_client).
        bucket_name: Target S3 bucket name.
        cap:         Maximum number of objects to collect.

    Returns:
        A tuple of (collected_objects, truncated) where:
        - collected_objects is a list of S3 object dicts, each containing
          "Key" (str), "Size" (int), and "LastModified" (datetime).
        - truncated is True when the cap was reached and more objects exist.

    Raises:
        AWSAuthenticationError: On invalid credentials.
        AWSAuthorizationError:  On IAM permission denial.
        AWSConfigurationError:  On missing or mislocated bucket.
        AWSUnexpectedError:     On any other boto3 or network error.
    """
    logger.info("Listing objects in bucket: %s (cap=%d)", bucket_name, cap)
    collected: list[dict[str, Any]] = []
    truncated: bool = False
    continuation_token: str | None = None

    try:
        while True:
            remaining = cap - len(collected)
            kwargs: dict[str, Any] = {
                "Bucket": bucket_name,
                "MaxKeys": min(remaining, 1000),
            }
            if continuation_token:
                kwargs["ContinuationToken"] = continuation_token

            logger.debug(
                "Requesting page: MaxKeys=%d, ContinuationToken=%s",
                kwargs["MaxKeys"],
                continuation_token,
            )
            response = client.list_objects_v2(**kwargs)

            contents = response.get("Contents", [])
            collected.extend(contents)
            logger.debug("Page returned %d objects; total collected: %d", len(contents), len(collected))

            is_truncated = response.get("IsTruncated", False)

            if len(collected) >= cap and is_truncated:
                truncated = True
                logger.info(
                    "Record cap reached (%d). Bucket has additional objects — truncating.",
                    cap,
                )
                break

            if not is_truncated:
                logger.debug("No more pages in bucket listing")
                break

            continuation_token = response.get("NextContinuationToken")

    except ClientError as exc:
        raise classify_client_error(exc) from exc
    except Exception as exc:
        logger.error("Unexpected error listing objects in bucket '%s': %s", bucket_name, str(exc))
        raise AWSUnexpectedError(str(exc)) from exc

    logger.info(
        "List objects completed: %d objects collected, truncated=%s",
        len(collected),
        truncated,
    )
    return collected, truncated


def upload_file(
    client: Any,
    local_file_path: str,
    bucket_name: str,
    s3_object_key: str,
) -> None:
    """
    Upload a local file to an S3 bucket at the specified object key.

    Uses boto3's upload_file method, which handles multipart upload
    transparently for large files. The caller is responsible for
    validating local file existence before calling this function.

    Args:
        client:          A boto3 S3 client (from build_s3_client).
        local_file_path: Absolute path to the local file on the agent host.
        bucket_name:     Target S3 bucket name.
        s3_object_key:   Destination object key within the bucket.

    Raises:
        AWSAuthenticationError: On invalid credentials.
        AWSAuthorizationError:  On IAM permission denial.
        AWSConfigurationError:  On missing or mislocated bucket.
        AWSUnexpectedError:     On any other boto3 or network error.
    """
    logger.info(
        "Uploading '%s' to s3://%s/%s",
        local_file_path,
        bucket_name,
        s3_object_key,
    )
    try:
        client.upload_file(local_file_path, bucket_name, s3_object_key)
    except ClientError as exc:
        raise classify_client_error(exc) from exc
    except Exception as exc:
        logger.error(
            "Unexpected error uploading '%s' to s3://%s/%s: %s",
            local_file_path,
            bucket_name,
            s3_object_key,
            str(exc),
        )
        raise AWSUnexpectedError(str(exc)) from exc

    logger.info(
        "Upload complete: s3://%s/%s",
        bucket_name,
        s3_object_key,
    )


def classify_client_error(exc: ClientError) -> ExecutionError:
    """
    Map a boto3 ClientError to the appropriate extension exception.

    Consults the internal error-code map. Falls back to AWSUnexpectedError
    for any code not explicitly mapped.

    Args:
        exc: A botocore ClientError instance.

    Returns:
        An instance of the matching extension exception class.
    """
    error_code: str = exc.response.get("Error", {}).get("Code", "")
    logger.debug("boto3 ClientError code: %s", error_code)

    exc_class = _CLIENT_ERROR_MAP.get(error_code, AWSUnexpectedError)
    logger.error("Classifying ClientError '%s' as %s", error_code, exc_class.__name__)
    return exc_class(str(exc))
