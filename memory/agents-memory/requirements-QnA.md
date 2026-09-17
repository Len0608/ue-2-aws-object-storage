# Requirements Completeness Assessment

**Classification: Moderate Detail**

The requirements clearly establish the integration name (AWS Object Storage), the target AWS service (S3), both core actions (List Objects and Upload File), the Python SDK (boto3), and the primary input fields (AWS Credentials, AWS Region, Bucket Name, Local File, S3 Object Key). The MVP/demo scope is also unambiguous — keep it simple, avoid unnecessary advanced features.

To finalize the implementation blueprint, several key decisions still need to be shaped: how AWS credentials map to UAC credential attributes (a structural decision affecting both the template and extension code), what information the List Objects action surfaces and how it is formatted (important for demo quality), which output-only fields appear in the UAC task instance view, and how to structure the machine-readable Extension Output JSON.

---

# Platform Compatibility

**Platform Compatibility from Requirements**: Linux
*(Explicit in `environment.md` — OS: Linux, Architecture: x86_64. Confirmed in requirements: "upload a local file from the Linux server where the Stonebranch Universal Agent is installed".)*

**Platform Compatibility Agreement**: Linux (x86_64)

> Note: Linux-only platform unlocks C extension modules with `manylinux_2_17_x86_64` wheels. However, all candidate modules for this extension (`boto3`, `tabulate`) are pure-Python and carry no binary compatibility concerns.

---

# Python Modules and Versions

## Researched Modules

**boto3**
- **Module Purpose**: Official AWS SDK for Python — provides the S3 client for listing bucket objects and uploading files. All runtime dependencies (`botocore`, `s3transfer`, `jmespath`) are also pure-Python.
- **Version**: 1.43.96
- **Type**: Pure Python

**tabulate**
- **Module Purpose**: Formats tabular data as styled ASCII tables for human-readable STDOUT output. Recommended by the UAC architecture guide for list-type outputs using `tablefmt="rounded_outline"`.
- **Version**: 0.10.0
- **Type**: Pure Python

## Agreed Python Modules and Versions

| Module | Purpose | Version | Type |
|---|---|---|---|
| boto3 | AWS S3 client (list objects, upload file) | 1.43.96 | Pure Python |
| tabulate | Formatted ASCII table output in STDOUT | 0.10.0 | Pure Python |

*(Confirmed via auto-applied recommended answers. See Q1 for tabulate inclusion rationale.)*

---

# Question Rationale

The requirements are well-defined at the functional level for an MVP integration. The eight clarifying questions below address decisions that cannot be safely defaulted without explicit direction: the credential attribute mapping (a structural decision), the output detail level and format (important for demo quality), the output-only fields (required for the template definition), the Extension Output JSON structure (needed for machine-readable downstream use), operational safety for large S3 buckets, and error message specificity. Answering these questions fully closes the gap between the current requirements and an implementable analysis document.

---

# Clarifying Questions for Requirements Refinement

## Critical Decision Path Questions

**Question 1**: Should `tabulate` be included for professional formatted table output in the List Objects STDOUT?

**Available Options:**
- **Option A (Recommended)**: Include `tabulate==0.10.0` — use `tablefmt="rounded_outline"` for a clean, professional table when listing S3 objects, showing Key, Size, and Last Modified columns.
- **Option B**: Plain text output only — list object keys one per line, no additional dependency required.

Example of Option A output:
```
╭──────────────────────────────────────┬──────────┬─────────────────────╮
│ Object Key                           │     Size │ Last Modified       │
├──────────────────────────────────────┼──────────┼─────────────────────┤
│ reports/monthly-2024-01.pdf          │  1.2 MB  │ 2024-01-15 10:23:00 │
│ data/backup-20240115.zip             │ 45.8 MB  │ 2024-01-15 09:45:00 │
╰──────────────────────────────────────┴──────────┴─────────────────────╯
```

- **Question Type**: New Discussion topic
- **Context & Resources**: The UAC architecture guide explicitly recommends `tabulate` with `tablefmt="rounded_outline"` for STDOUT when information can be displayed in rows and columns. `tabulate` is pure-Python (v0.10.0, actively maintained, widely used), adding no binary compatibility concerns. For a demo, the visual quality of STDOUT directly affects how well the integration communicates its value. [tabulate project](https://github.com/astanin/python-tabulate)
- **Question Dependencies**: None
- **Recommended Answer**: Option A — Include `tabulate==0.10.0` for professional table output
- **Rationale**: For a demo/MVP integration, polished STDOUT output makes the capability immediately obvious to any audience. `tabulate` adds negligible overhead and is explicitly endorsed by the architecture guide.
- **Trade-offs**: Option A adds one dependency but significantly improves readability. Option B is marginally simpler but produces plain text that is less impactful for a demo audience.
- **Requirement Impact**: Add `tabulate==0.10.0` to `requirements.txt`.
- **User's Answer**: Option A — Include `tabulate==0.10.0` for professional table output

---

**Question 2**: How should the AWS Access Key ID and Secret Access Key be mapped to the UAC credential attributes?

**Available Options:**
- **Option A (Recommended)**: `user` = AWS Access Key ID, `password` = AWS Secret Access Key
- **Option B**: `user` = AWS Access Key ID, `token` = AWS Secret Access Key

- **Question Type**: New Discussion topic
- **Context & Resources**: UAC credentials have the following attributes: `user` (always required), `password` (for secrets up to 255 characters), `token` (for longer tokens or session credentials), `passphrase`, `key_location`. AWS Secret Access Keys are exactly 40 characters — well within the `password` attribute limit. The `token` attribute is semantically best reserved for temporary AWS STS session tokens if those are ever needed in the future. [AWS Access Key documentation](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html)
- **Question Dependencies**: None
- **Recommended Answer**: Option A — `user` = AWS Access Key ID, `password` = AWS Secret Access Key
- **Rationale**: The `password` attribute is the standard UAC choice for static secrets under 255 characters. The `user` attribute naturally maps to the Access Key ID as the identifier. Using `token` would be non-standard and confusing for operators; it is better reserved for STS session tokens.
- **Trade-offs**: Both options are functionally equivalent for storing and retrieving credentials. Option A follows the natural user=identifier, password=secret convention that operators will expect.
- **Requirement Impact**: The credential field hint text should guide operators: "Runtime User: AWS Access Key ID | Runtime Password: AWS Secret Access Key."
- **User's Answer**: Option A — `user` = AWS Access Key ID, `password` = AWS Secret Access Key

---

**Question 3**: Should the AWS credential field be required, or optional (allowing fallback to boto3's default credential chain)?

**Available Options:**
- **Option A (Recommended)**: Required — the task fails immediately with a clear validation error if no credential is provided.
- **Option B**: Optional — when no credential is provided, boto3 automatically falls back to its default credential chain: environment variables (`AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`), `~/.aws/credentials` on the agent host, or IAM instance profile (when running on EC2/ECS/EKS with an attached IAM role).

- **Question Type**: New Discussion topic
- **Context & Resources**: boto3's credential resolution order is: (1) explicit parameters passed to the client, (2) environment variables `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY`, (3) AWS config files (`~/.aws/credentials`), (4) IAM instance profile. Option B allows the extension to work on EC2/ECS agents that have IAM roles attached — without requiring explicit credentials in the task definition. Option A is more predictable and auditable for a demo context. [boto3 credentials guide](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html)
- **Question Dependencies**: None
- **Recommended Answer**: Option A — Required credential field for MVP
- **Rationale**: For a demo integration, explicit credentials are clearer, more auditable, and easier to troubleshoot. The IAM role path requires the agent to be running on properly configured AWS infrastructure, which may not be present in all demo environments.
- **Trade-offs**: Option A is predictable — every execution has an explicit, visible credential. Option B is more flexible for production deployments on AWS-hosted agents but adds validation complexity and may produce confusing behavior when no credential is provided and no implicit credential exists.
- **Requirement Impact**: None — the requirements already list "AWS Credentials" as a field.
- **User's Answer**: Option A — Required credential field for MVP

---

## Essential Input/Output Questions

**Question 4**: For the List Objects action, what information should be displayed per S3 object?

**Available Options:**
- **Option A**: Object Key only — just the S3 path/name of each object.
- **Option B (Recommended)**: Object Key + Size (formatted, e.g., "1.2 MB") + Last Modified timestamp — the most informative and demo-friendly subset.
- **Option C**: Full metadata — Key + Size + Last Modified + Storage Class + ETag.

- **Question Type**: New Discussion topic
- **Context & Resources**: The S3 `list_objects_v2` API returns: `Key`, `Size` (bytes), `LastModified` (datetime), `StorageClass` (STANDARD, GLACIER, INTELLIGENT_TIERING, etc.), `ETag` (content hash). For a demo, seeing file name + size + last modified immediately communicates that real S3 data is being read. Storage class and ETag are rarely meaningful to a non-technical demo audience. [boto3 list_objects_v2 API](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/list_objects_v2.html)
- **Question Dependencies**: None
- **Recommended Answer**: Option B — Object Key + Size + Last Modified
- **Rationale**: Option B provides the most informative and visually compelling subset without technical clutter. Size and last modified are exactly what operators would look for when browsing files.
- **Trade-offs**: Option A is simplest but less impressive for a demo. Option C is exhaustive but adds noise (ETag, Storage Class) that requires explanation. Option B is the optimal balance.
- **Requirement Impact**: None — requirements do not specify output detail level.
- **User's Answer**: Option B — Object Key + Size + Last Modified

---

**Question 5**: What output-only fields should be visible in the UAC task instance view after execution?

**Available Options:**
- **Option A**: Status message only — a single shared field with a human-readable description (e.g., "Success: Found 42 objects" or "Success: File uploaded to s3://bucket/key").
- **Option B (Recommended)**: Status message (shared across both actions) + one action-specific field:
  - For **List Objects**: "Objects Found" — numeric count of objects returned (e.g., "42")
  - For **Upload File**: "Uploaded S3 Key" — the destination S3 key (e.g., "reports/file.pdf")

- **Question Type**: New Discussion topic
- **Context & Resources**: UAC output-only fields appear directly in the task instance list view without requiring users to open the STDOUT log. The architecture guide recommends 2–3 fields maximum for clarity. A shared Status field works well across both actions; one action-specific field adds high-value at-a-glance context that is especially useful in a demo.
- **Question Dependencies**: None
- **Recommended Answer**: Option B — Shared Status field + action-specific field
- **Rationale**: The shared Status field provides immediate success/failure context. "Objects Found" for List and "Uploaded S3 Key" for Upload give the most relevant result visible at a glance — without requiring the demo audience to open any logs.
- **Trade-offs**: Option B adds two additional fields to the template compared to Option A's single field, but provides significantly better visibility into execution results.
- **Requirement Impact**: Adds 3 output-only fields to the template: `status` (Text Field, shared), `object_count` (Text Field, List Objects action), `uploaded_key` (Text Field, Upload File action). All marked Output Only and `extensionStatus: true`.
- **User's Answer**: Option B — Shared Status field + action-specific field

---

**Question 6**: What should the machine-readable Extension Output JSON contain for each action?

**Available Options:**

**Option A (Recommended)**: Structured output with action-specific result objects:

For **List Objects** (success):
```json
{
  "result": {
    "bucket": "my-bucket",
    "object_count": 42,
    "truncated": false,
    "objects": [
      { "key": "reports/file.pdf", "size_bytes": 1258291, "last_modified": "2024-01-15T10:23:00Z" }
    ]
  }
}
```

For **Upload File** (success):
```json
{
  "result": {
    "bucket": "my-bucket",
    "key": "folder/file.txt",
    "s3_uri": "s3://my-bucket/folder/file.txt"
  }
}
```

For any **failure**:
```json
{
  "error": {
    "type": "AuthenticationError",
    "message": "Invalid AWS credentials — check Access Key ID and Secret Access Key"
  }
}
```

**Option B**: Minimal — just a status string and the primary result value (object count or uploaded key).

- **Question Type**: New Discussion topic
- **Context & Resources**: Extension Output is machine-parseable JSON made available to downstream tasks in a UAC workflow. The architecture guide recommends wrapping successful results in a `result` object and failures in an `error` object. The `s3_uri` (e.g., `s3://bucket/key`) is a directly usable reference for downstream AWS SDK calls or other Stonebranch tasks. The `truncated` flag (per Q7) is critical — it signals to downstream automation that the object list may be incomplete.
- **Question Dependencies**: Q7 — the `truncated` flag in the List Objects result assumes Q7=Option A (cap is applied). With Q7=Option A as the recommended answer, `truncated` should be included.
- **Recommended Answer**: Option A — structured output with `s3_uri` and `truncated` flag
- **Rationale**: Structured output requires minimal extra implementation effort and provides significantly more value for downstream automation. The `s3_uri` is immediately usable. The `truncated` flag prevents silent data gaps in automation workflows.
- **Trade-offs**: Option A is slightly more verbose but provides clean, actionable data. Option B is simpler but less useful for any downstream processing.
- **Requirement Impact**: None.
- **User's Answer**: Option A — structured output with `s3_uri` and `truncated` flag

---

## Functional Behavior Questions

**Question 7**: How should the extension handle listing S3 buckets that contain a very large number of objects?

**Available Options:**
- **Option A (Recommended)**: Cap inline output using the `UE_MAX_OUTPUT_RECORDS` environment variable (default: 100 objects). When the cap is reached, emit a truncation warning in STDOUT, set `"truncated": true` in the Extension Output JSON, and report the total object count seen.
- **Option B**: Return up to 1,000 objects — S3's single API call limit — with no further cap.
- **Option C**: Paginate through all S3 pages and return all objects regardless of count.

- **Question Type**: New Discussion topic
- **Context & Resources**: S3's `list_objects_v2` API returns up to 1,000 objects per request and uses a continuation token for pagination. UAC stores task STDOUT and Extension Output in its database — very large outputs can degrade performance or hit storage limits. The architecture guide defines the "Large Output Safety Net Pattern" using `UE_MAX_OUTPUT_RECORDS` (default: 100) specifically for record-based output. The environment variable approach allows operators to override the default per-task without changing extension code.
- **Question Dependencies**: Q6 — the `truncated` flag in Extension Output is only meaningful if a cap is applied (Q7=Option A).
- **Recommended Answer**: Option A — `UE_MAX_OUTPUT_RECORDS` environment variable with default of 100
- **Rationale**: 100 objects is more than sufficient for a demo bucket. The environment variable gives operators flexibility to increase the limit when needed. The truncation warning and flag ensure users are never silently misled about bucket contents.
- **Trade-offs**: Option A requires a small amount of extra logic for the cap check and truncation warning. Option B is slightly simpler but could generate very large STDOUT for production buckets. Option C is the most complete but potentially extremely slow for large buckets and produces outputs too large for the UAC database.
- **Requirement Impact**: None — requirements do not specify pagination behavior.
- **User's Answer**: Option A — `UE_MAX_OUTPUT_RECORDS` environment variable with default of 100

---

**Question 8**: How specific should error messages be when S3 operations fail?

**Available Options:**
- **Option A**: Generic error handling — catch all exceptions and surface the original boto3 error message as-is. Status description format: `"Error: <original boto3 error message>"`.
- **Option B (Recommended)**: Categorized error handling — map boto3 error codes to user-friendly messages with clear guidance. Specific scenarios and suggested messages:
  - Invalid credentials → return code 1, `"Authentication Error: Invalid AWS Access Key ID or Secret Access Key"`
  - Access denied → return code 1, `"Authorization Error: Access denied — check IAM permissions for bucket '<name>'"`
  - Bucket not found → return code 1, `"Configuration Error: Bucket '<name>' does not exist or is in a different region"`
  - Local file not found (Upload only) → return code 20, `"Validation Error: Local file '<path>' not found on the agent host"`
  - Unexpected errors → return code 1, `"Unexpected Error: <original boto3 message>"`

- **Question Type**: New Discussion topic
- **Context & Resources**: boto3 raises `ClientError` exceptions with a machine-readable error `Code` in the response: `InvalidClientTokenId` (wrong key ID), `AuthFailure` (wrong secret), `AccessDenied`, `NoSuchBucket`. Categorizing these into user-friendly messages is especially important for a demo where the audience may be troubleshooting configuration issues live. The additional implementation effort is minimal — just a small mapping of error codes to friendly strings. [boto3 error handling guide](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/error-handling.html)
- **Question Dependencies**: None
- **Recommended Answer**: Option B — categorized error handling
- **Rationale**: Even for an MVP, the difference between a raw boto3 error code and a clear, actionable message is significant — especially during a live demo. Specific messages tell the operator exactly what to fix rather than requiring them to decode AWS error codes.
- **Trade-offs**: Option B requires mapping a handful of boto3 error codes to friendly messages. Option A is marginally simpler but produces raw error messages that may confuse non-technical demo audiences.
- **Requirement Impact**: None.
- **User's Answer**: Option B — categorized error handling
