#!/usr/bin/env python3

"""
Generate a workflow run update object - using a combination of

1. Portal run id
2. Libraries
3. Payload
4. Upstream data (optional)
"""

# Layer imports
from orcabus_api_tools.workflow import get_workflow_run_from_portal_run_id


def handler(event, context):
    # Get the event inputs
    # Get the event inputs
    portal_run_id = event.get("portalRunId", None)
    libraries = event.get("libraries", None)
    payload = event.get("payload", None)
    upstream_data = event.get("upstreamData", {})
    status = event.get("status", None)
    engine_parameters = event.get("engineParameters", None)

    # Get the upstream stuff
    data_files = upstream_data.get('dataFiles', None)

    # Create a copy of the pieriandx draft workflow run object to update
    draft_workflow_run = get_workflow_run_from_portal_run_id(
        portal_run_id=portal_run_id
    )

    # Make a copy
    draft_workflow_update = draft_workflow_run.copy()

    # Remove 'currentState' and replace with 'status'
    draft_workflow_update['status'] = draft_workflow_update.pop('currentState')['status']

    # If the data files already exist in the payload, use those
    if (
            payload.get("data", {}).get("inputs", {}).get("dataFiles", None) is not None and
            # The datafiles dict is not empty
            payload["data"]["inputs"]["dataFiles"]
    ):
        data_files = payload["data"]["inputs"]["dataFiles"]

    # Add in data files to the payload
    if data_files is not None:
        payload["data"] = payload.get("data", {})
        payload["data"]["inputs"] = payload["data"].get("inputs", {})
        payload["data"]["inputs"]["dataFiles"] = data_files

    # Get status
    if status is not None:
        draft_workflow_update['status'] = status

    # Set the payload in the draft workflow run update object
    draft_workflow_update["payload"] = {
        "version": payload["version"],
        "data": payload.get("data", {})
    }

    # Set the engine parameters if provided
    if engine_parameters is not None:
        if draft_workflow_update["payload"]["data"].get("engineParameters", None) is None:
            draft_workflow_update["payload"]["data"]["engineParameters"] = {}
        draft_workflow_update["payload"]["data"]["engineParameters"].update(engine_parameters)

    # Set out the libraries
    # Add in the libraries if provided
    if libraries is not None:
        draft_workflow_update["libraries"] = list(map(
            lambda library_iter: {
                "libraryId": library_iter['libraryId'],
                "orcabusId": library_iter['orcabusId'],
                "readsets": library_iter.get('readsets', [])
            },
            libraries
        ))

    # Return the draft workflow run update object
    return {
        "workflowRunUpdate": draft_workflow_update
    }
