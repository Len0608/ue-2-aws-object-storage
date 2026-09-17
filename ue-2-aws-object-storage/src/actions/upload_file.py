"""Upload File action for the AWS Object Storage Universal Extension.

Uploads a local file from the Universal Agent host to the specified AWS S3
bucket at the specified S3 object key. Validates local file existence before
any AWS API call.
"""

import logging
import os

from actions.output import ActionOutput
from exceptions import AWSValidationError, ExecutionError
from fields.input import InputFields
from fields.output import OutputFields
from manager import ExtensionManager
from utility import build_s3_client, upload_file

logger = logging.getLogger("UNV")
extension_manager = ExtensionManager()


def upload_file_action(input_data: InputFields) -> ActionOutput:
    """Upload a local file to the configured S3 bucket.

    Validates that the local file exists on the agent host before initiating
    any AWS API call. On success, prints a confirmation line to STDOUT and
    populates the status and uploaded_s3_key output-only fields.

    Args:
        input_data: Validated input fields from the UAC task form.

    Returns:
        ActionOutput populated with bucket, key, and s3_uri for Extension
        Output, plus status/uploaded_s3_key set on OutputFields for real-time
        UI display.

    Raises:
        AWSValidationError:     When the local file does not exist on the host.
        AWSAuthenticationError: On invalid AWS credentials.
        AWSAuthorizationError:  On IAM permission denial.
        AWSConfigurationError:  On missing or mislocated bucket.
        AWSUnexpectedError:     On any other boto3 or network error.
    """
    logger.info("Starting upload_file action")
    logger.debug(
        "Input: action=%s, aws_region=%s, bucket_name=%s, "
        "local_file_path=%s, s3_object_key=%s",
        input_data.action.value if input_data.action else None,
        input_data.aws_region.value if input_data.aws_region else None,
        input_data.bucket_name.value if input_data.bucket_name else None,
        input_data.local_file_path.value if input_data.local_file_path else None,
        input_data.s3_object_key.value if input_data.s3_object_key else None,
    )

    # Initialize output fields for real-time UI tracking.
    output_fields = OutputFields()
    output_fields.update(status="Starting")

    # Unwrap field values.
    access_key_id: str = input_data.aws_credentials["user"]
    secret_access_key: str = input_data.aws_credentials["password"]
    region: str = input_data.aws_region.value
    bucket_name: str = input_data.bucket_name.value
    local_file_path: str = input_data.local_file_path.value
    s3_object_key: str = input_data.s3_object_key.value

    # --- Step 1: Validate local file existence ---
    logger.info("Validating local file path: %s", local_file_path)
    output_fields.update(status="Validating local file")

    if not os.path.exists(local_file_path):
        error_msg = "Local file '%s' not found on the agent host" % local_file_path
        logger.error(error_msg)
        raise AWSValidationError(error_msg)

    logger.info("Local file exists: %s", local_file_path)

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

    # --- Step 3: Upload file to S3 ---
    logger.info(
        "Uploading '%s' to s3://%s/%s",
        local_file_path,
        bucket_name,
        s3_object_key,
    )
    output_fields.update(status="Uploading file")

    if extension_manager.is_cancelled():
        logger.warning("Operation cancelled before file upload")
        raise ExecutionError("Operation cancelled by user")

    upload_file(
        client=client,
        local_file_path=local_file_path,
        bucket_name=bucket_name,
        s3_object_key=s3_object_key,
    )

    # --- Step 4: Print confirmation to STDOUT ---
    s3_uri = "s3://%s/%s" % (bucket_name, s3_object_key)
    print("Uploaded %s to %s" % (local_file_path, s3_uri))

    # --- Step 5: Populate output-only fields ---
    status_msg = "Success: File uploaded to %s" % s3_uri
    output_fields.update(
        status=status_msg,
        uploaded_s3_key=s3_object_key,
    )
    logger.info("Output fields updated: status='%s'", status_msg)

    logger.info("upload_file action completed successfully")
    logger.debug(
        "Returning: bucket=%s, key=%s, s3_uri=%s",
        bucket_name,
        s3_object_key,
        s3_uri,
    )

    # --- Step 6: Build Extension Output result ---
    return ActionOutput(
        bucket=bucket_name,
        key=s3_object_key,
        s3_uri=s3_uri,
    )
