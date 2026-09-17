# Requirements Meeter Output

## Zipsafe Decision
- **Result**: false
- **Reason**: Packages with data files — botocore (boto3's dependency) ships `botocore/cacert.pem` and a `botocore/data/` directory containing JSON endpoint configuration files (`endpoints.json`, `partitions.json`, `_retry.json`, `sdk-default-configuration.json`)

## CLI Tools
- None required — no CLI binaries to download or vendor

## Python Dependencies
- boto3==1.43.96 — Has data files (botocore transitive dependency carries `.pem` and `.json` data files)
- tabulate==0.10.0 — Pure Python (no data files)

## Setup.py Changes
- VENDOR_FOLDER added: no (no CLI binaries to vendor; vendor path is absent)
- data_files updated: no (existing zip_safe: False branch in setup.py already handles dep wheel packaging correctly)
