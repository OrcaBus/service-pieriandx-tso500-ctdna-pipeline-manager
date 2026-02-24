#!/usr/bin/env python3

"""
Get redcap tags for a given library id

Return the following tags

panelVersion
isIdentified
sampleType
"""

# Standard library imports
from os import environ
import json
from pathlib import Path
from typing import Literal, List, Dict

# Layer imports
from orcabus_api_tools.metadata import get_library_from_library_id
from orcabus_api_tools.utils.aws_helpers import get_ssm_value

# Globals
PROJECT_INFO_SSM_ENV_VAR_PREFIX_ENV_VAR = "PROJECT_INFO_SSM_PARAMETER_PREFIX"
PROJECT_INFO_DEFAULT_SSM_ENV_VAR = "PROJECT_INFO_DEFAULT_SSM_PARAMETER_NAME"


ProjectInfoKeysType = Literal[
    'panel',
    'sampleType',
    'isIdentified',
    'defaultSnomedDiseaseCode',
]
PROJECT_INFO_KEYS: List[ProjectInfoKeysType] = [
    'panel',
    'sampleType',
    'isIdentified',
    'defaultSnomedDiseaseCode',
]


def get_default_project_info(project_id: str) -> Dict[ProjectInfoKeysType, str]:
    return json.loads(get_ssm_value(environ[PROJECT_INFO_DEFAULT_SSM_ENV_VAR]))


def get_project_info_from_ssm_parameter(project_id: str) -> Dict[ProjectInfoKeysType, str]:
    return json.loads(get_ssm_value(str(Path(environ[PROJECT_INFO_SSM_ENV_VAR_PREFIX_ENV_VAR]) / project_id)))


def get_match_from_pieriandx_project_info(project_id) -> Dict[ProjectInfoKeysType, str]:
    try:
        return get_project_info_from_ssm_parameter(project_id)
    except ValueError as e:
        # Could not get project info
        return get_default_project_info(project_id)


def handler(event, context):
    """
    Get redcap tags for a given library id
    :param event:
    :param context:
    :return:
    """

    # Get the inputs
    library_id = event['libraryId']

    # Get the library object
    library_obj = get_library_from_library_id(library_id)

    # Get the project set from the library object
    project_set = library_obj.get('projectSet', [])
    if not project_set:
        raise ValueError(f"No projectSet found for library id {library_id}")

    # Get the last project connected from the project set
    project_id = project_set[-1]['projectId']

    # Get the info from the ssm parameter
    # Panel, sampleType, isIdentified, defaultSnomedDiseaseCode
    project_info = get_match_from_pieriandx_project_info(project_id)

    # Build the return object
    return {
        'panelVersion': project_info['panel'],
        'isIdentified': project_info['isIdentified'],
        'sampleType': project_info['sampleType'],
        'projectId': project_id,
        'defaultSnomedDiseaseCode': project_info.get('defaultSnomedDiseaseCode', None)
    }
