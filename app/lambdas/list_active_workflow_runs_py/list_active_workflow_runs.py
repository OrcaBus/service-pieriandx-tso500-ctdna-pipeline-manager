#!/usr/bin/env python3

"""
Get a list of active workflow runs in the workflow run manager
"""

# Standard imports
from typing import Literal, List, Dict

# Layer imports
from orcabus_api_tools.workflow import get_workflow_by_workflow_name

# Globals
WORKFLOW_NAME = "pieriandx-tso500-ctdna"

# Running types
RunningTypes = Literal[
    'RUNNABLE',
    'RUNNING'
]
RUNNING_TYPES_LIST: List[RunningTypes] = [
    "RUNNABLE",
    "RUNNING"
]


def handler(event, context) -> Dict[str, List[Dict[str, str]]]:
    """
    Get a list of active workflow runs in the workflow run manager
    :param event:
    :param context:
    :return:
    """

    # Get all workflows
    workflows = get_workflow_by_workflow_name(WORKFLOW_NAME)

    # Get active workflow runs
    active_workflow_runs = list(map(
        lambda workflow_iter_: {
          "portalRunId": workflow_iter_['portalRunId'],
        },
        list(filter(
            lambda workflow: workflow["currentState"]["status"] in RUNNING_TYPES_LIST,
            workflows
        ))
    ))

    return {
        "workflowRunsList": active_workflow_runs
    }
