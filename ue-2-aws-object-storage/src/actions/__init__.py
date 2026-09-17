"""Actions module — business logic implementations for AWS Object Storage."""

from actions.output import ActionOutput
from actions.list_objects import list_objects_action
from actions.upload_file import upload_file_action

# Maps action field values (as returned by input_data.action.value) to the
# corresponding action function.  Keys must match the Choice Field option
# values defined in template.json.
ACTION_MAPPER = {
    "List Objects": list_objects_action,
    "Upload File": upload_file_action,
}
