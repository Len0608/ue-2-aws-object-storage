"""
Utility package for the AWS Object Storage Universal Extension.

Modules:
    s3_client   — boto3 S3 client lifecycle, list/upload operations, and error classification
    formatter   — human-readable size/timestamp formatting and ASCII table generation
"""
from utility.s3_client import build_s3_client, list_objects, upload_file, classify_client_error
from utility.formatter import format_size, format_timestamp, build_ascii_table

__all__ = [
    "build_s3_client",
    "list_objects",
    "upload_file",
    "classify_client_error",
    "format_size",
    "format_timestamp",
    "build_ascii_table",
]
