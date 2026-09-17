"""ActionOutput dataclass for action return values."""

from dataclasses import dataclass
from typing import Optional, Any, Dict, List


@dataclass
class ActionOutput:
    """Output from action functions for the AWS Object Storage extension.

    List Objects fields:
        bucket:       The S3 bucket name that was queried.
        object_count: Number of objects collected (up to cap).
        truncated:    True when the result was capped and more objects exist.
        objects:      List of object dicts with key, size_bytes, last_modified.

    Upload File fields:
        key:    The destination S3 object key.
        s3_uri: Full S3 URI of the uploaded object.

    The bucket field is shared by both actions.
    There are no stdout_options or output_options control fields in this
    extension's template — print_output() always prints everything, and
    to_dict() always includes everything.
    """

    # Shared field
    bucket: Optional[str] = None

    # List Objects fields
    object_count: Optional[int] = None
    truncated: Optional[bool] = None
    objects: Optional[List[Dict[str, Any]]] = None

    # Upload File fields
    key: Optional[str] = None
    s3_uri: Optional[str] = None

    def print_output(self) -> None:
        """Print action results to STDOUT.

        List Objects: prints the ASCII table and optional truncation notice.
        Upload File:  prints the upload confirmation line.

        Note: ASCII table printing for List Objects is handled inside the
        action function itself (before building ActionOutput), so this method
        handles only the Upload File confirmation line. The List Objects action
        emits the table and truncation text directly to STDOUT during execution
        and does not need to re-print via print_output.
        """
        # Upload File: print confirmation line
        if self.s3_uri is not None:
            print(
                "Uploaded %s to %s"
                % (
                    self.key if self.key else "",
                    self.s3_uri,
                )
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for Extension Output (unv_output).

        Returns the result object structure defined in the analysis:
        - List Objects: {bucket, object_count, truncated, objects}
        - Upload File:  {bucket, key, s3_uri}

        Fields that are None are omitted from the output.
        """
        output: Dict[str, Any] = {}

        if self.bucket is not None:
            output["bucket"] = self.bucket

        # List Objects fields
        if self.object_count is not None:
            output["object_count"] = self.object_count
        if self.truncated is not None:
            output["truncated"] = self.truncated
        if self.objects is not None:
            output["objects"] = self.objects

        # Upload File fields
        if self.key is not None:
            output["key"] = self.key
        if self.s3_uri is not None:
            output["s3_uri"] = self.s3_uri

        return output
