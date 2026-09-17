"""List Objects action for the AWS Object Storage Universal Extension.

Lists objects stored in the specified AWS S3 bucket and prints a formatted
ASCII table to STDOUT. Output is capped at UE_MAX_OUTPUT_RECORDS (default 100).
"""

import logging
import os
import sys

from actions.output import ActionOutput
from exceptions import ExecutionError
from fields.input import InputFields
from fields.output import OutputFields
from manager import ExtensionManager
from utility import build_s3_client, list_objects, format_size, format_timestamp, build_ascii_table

logger = logging.getLogger("UNV")
extension_manager = ExtensionManager()

# Default record cap used when UE_MAX_OUTPUT_RECORDS is absent or invalid.
_DEFAULT_CAP: int = 100


def list_objects_action(input_data: InputFields) -> ActionOutput:
    """List objects in the configured S3 bucket.

    Reads up to UE_MAX_OUTPUT_RECORDS objects from the bucket, prints a
    rounded ASCII table to STDOUT, and emits truncation warnings when the
    result set is capped and more objects exist.

    Args:
        input_data: Validated input fields from the UAC task form.

    Returns:
        ActionOutput populated with bucket, object_count, truncated, and
        objects list for Extension Output, plus status/objects_found set
        on the OutputFields for real-time UI display.

    Raises:
        AWSAuthenticationError: On invalid AWS credentials.
        AWSAuthorizationError:  On IAM permission denial.
        AWSConfigurationError:  On missing or mislocated bucket.
        AWSUnexpectedError:     On any other boto3 or network error.
    """
    logger.info("Starting list_objects action")
    logger.debug(
        "Input: action=%s, aws_region=%s, bucket_name=%s",
        input_data.action.value if input_data.action else None,
        input_data.aws_region.value if input_data.aws_region else None,
        input_data.bucket_name.value if input_data.bucket_name else None,
    )

    # Initialize output fields for real-time UI tracking.
    output_fields = OutputFields()
    output_fields.update(status="Starting")

    # --- Step 1: Resolve output record cap ---
    raw_cap = os.environ.get("UE_MAX_OUTPUT_RECORDS", "")
    cap: int
    try:
        cap = int(raw_cap)
        if cap <= 0:
            raise ValueError("cap must be positive")
        logger.debug("UE_MAX_OUTPUT_RECORDS resolved to %d", cap)
    except (ValueError, TypeError):
        cap = _DEFAULT_CAP
        logger.debug(
            "UE_MAX_OUTPUT_RECORDS absent or invalid ('%s'); defaulting to %d",
            raw_cap,
            cap,
        )

    # Unwrap field values.
    access_key_id: str = input_data.aws_credentials["user"]
    secret_access_key: str = input_data.aws_credentials["password"]
    region: str = input_data.aws_region.value
    bucket_name: str = input_data.bucket_name.value

    # --- Step 2: Initialize S3 client ---
    logger.info("Initializing S3 client")
    output_fields.update(status="Connecting to S3")

    if extension_manager.is_cancelled():
        logger.warning("Operation cancelled before S3 client initialization")
        raise ExecutionError("Operation cancelled by user")

    client = build_s3_client(
        access_key_id=access_key_id,
        secret_access_key=secret_access_key,
        region=region,
    )

    # --- Step 3: Paginate and collect objects up to cap ---
    logger.info("Listing objects in bucket: %s (cap=%d)", bucket_name, cap)
    output_fields.update(status="Listing objects")

    if extension_manager.is_cancelled():
        logger.warning("Operation cancelled before listing objects")
        raise ExecutionError("Operation cancelled by user")

    collected, truncated = list_objects(
        client=client,
        bucket_name=bucket_name,
        cap=cap,
    )

    logger.info(
        "Collected %d objects (truncated=%s)",
        len(collected),
        truncated,
    )

    # --- Step 4: Format and print ASCII table to STDOUT ---
    logger.info("Formatting ASCII table for %d objects", len(collected))
    output_fields.update(status="Formatting output")

    rows = []
    for obj in collected:
        rows.append(
            {
                "key": obj["Key"],
                "size": format_size(obj["Size"]),
                "last_modified": format_timestamp(obj["LastModified"]),
            }
        )

    table_str = build_ascii_table(rows)
    print(table_str)

    # --- Step 5: Emit truncation warning ---
    if truncated:
        truncation_msg = (
            "Note: Results are limited to %d records. "
            "The bucket may contain additional objects." % cap
        )
        print(truncation_msg)
        stderr_msg = (
            "WARNING: Output truncated to %d records "
            "(UE_MAX_OUTPUT_RECORDS=%d). Additional objects exist in the bucket."
            % (cap, cap)
        )
        print(stderr_msg, file=sys.stderr)
        logger.warning(
            "Output truncated to %d records; bucket has additional objects",
            cap,
        )

    # --- Step 6: Populate output-only fields ---
    status_msg = "Success: Found %d objects in bucket '%s'" % (len(collected), bucket_name)
    output_fields.update(
        status=status_msg,
        objects_found=str(len(collected)),
    )
    logger.info("Output fields updated: status='%s'", status_msg)

    # --- Step 7: Build Extension Output result ---
    objects_result = [
        {
            "key": obj["Key"],
            "size_bytes": obj["Size"],
            "last_modified": format_timestamp(obj["LastModified"]),
        }
        for obj in collected
    ]

    logger.info("list_objects action completed successfully")
    logger.debug(
        "Returning: bucket=%s, object_count=%d, truncated=%s",
        bucket_name,
        len(collected),
        truncated,
    )

    return ActionOutput(
        bucket=bucket_name,
        object_count=len(collected),
        truncated=truncated,
        objects=objects_result,
    )
