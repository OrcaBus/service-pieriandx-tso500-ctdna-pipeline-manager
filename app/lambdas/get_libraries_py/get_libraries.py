#!/usr/bin/env python3

"""
Get the libraries from the input, check their metadata,
"""

# Standard ipmorts
from typing import List

# Layer imports
from orcabus_api_tools.metadata.models import LibraryBase


def handler(event, context):
    """
    Get the libraries from the input, check their metadata,
    :param event:
    :param context:
    :return:
    """
    libraries: List[LibraryBase] = event.get("libraries", [])
    if not libraries:
        raise ValueError("No libraries provided in the input")

    if len(libraries) > 1:
        raise ValueError("We expect at most one library in the input")

    # If only one library is provided, then we have a germline library
    return {
        "libraryId": libraries[0]['libraryId']
    }
