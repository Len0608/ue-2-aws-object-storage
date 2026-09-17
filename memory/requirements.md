Create a new **Stonebranch Universal Extension for Universal Automation Center (UAC)** named **AWS Object Storage**.

The extension should provide a very simple AWS S3 integration with two functions:

a) **List Objects** – list files/objects in a specified AWS S3 bucket.

b) **Upload File** – upload a local file from the Linux server where the Stonebranch Universal Agent is installed to a specified AWS S3 bucket and S3 object key.

The extension should use the Python `boto3` SDK. `boto3` and all required dependencies must be bundled with the Universal Extension so that nothing needs to be installed separately on the Universal Agent.

Use simple task fields such as **AWS Credentials**, **AWS Region**, **Bucket Name**, and the action-specific fields. No prefix field is required. For Upload File, include **Local File** and **S3 Object Key**.

This should be an **MVP/demo integration only**. The purpose is simply to demonstrate that AWS S3 integration can be implemented with Stonebranch. Please keep the implementation as simple as possible and avoid unnecessary advanced features.
