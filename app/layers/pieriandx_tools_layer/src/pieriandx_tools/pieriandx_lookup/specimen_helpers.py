#!/usr/bin/env python3

"""
Given a specimen code, get the specimen label
"""
from os import environ
# Imports
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
from tempfile import NamedTemporaryFile

from orcabus_api_tools.utils.aws_helpers import get_ssm_value
from ..utils.compression_helpers import decompress_file

# Compressed version of
# https://velserapm.atlassian.net/wiki/download/attachments/86704490/SnomedCT-Term_For_SpecimenType.xls?version=1&modificationDate=1561395451000&api=v2
SNOMED_CT_SPECIMEN_TYPE_S3_PATH_SSM_ENV_VAR = "SNOMED_CT_SPECIMEN_TYPE_SSM_PARAMETER_NAME"
SNOMED_CT_SPECIMEN_TYPE_DF = None


def get_specimen_tree() -> pd.DataFrame:
    """
    Returns a dataframe with the following columns
    * Code
    * CodeSystem
    * Label
    :return:
    """
    from ..aws_helpers.s3_helpers import download_file

    global SNOMED_CT_SPECIMEN_TYPE_DF

    if SNOMED_CT_SPECIMEN_TYPE_DF is not None:
        return SNOMED_CT_SPECIMEN_TYPE_DF

    # Download the file from S3
    with (
        NamedTemporaryFile(suffix='json.gz') as snomed_ct_specimen_tree_file_compressed,
        NamedTemporaryFile(suffix='json') as snomed_ct_specimen_tree_file_decompressed,
    ):
        # Get the s3 uri path
        s3_obj = urlparse(get_ssm_value(environ[SNOMED_CT_SPECIMEN_TYPE_S3_PATH_SSM_ENV_VAR]))

        # Download the file from S3
        download_file(
            bucket=s3_obj.netloc,
            key=s3_obj.path.lstrip('/'),
            output_file_path=Path(snomed_ct_specimen_tree_file_compressed.name)
        )

        # Flush to ensure all data is written
        snomed_ct_specimen_tree_file_compressed.flush()

        # Decompress the file
        decompress_file(
            Path(snomed_ct_specimen_tree_file_compressed.name),
            Path(snomed_ct_specimen_tree_file_decompressed.name)
        )

        # Flush to ensure all data is written
        snomed_ct_specimen_tree_file_decompressed.flush()

        # Read the decompressed file into a dataframe
        SNOMED_CT_SPECIMEN_TYPE_DF = pd.read_json(snomed_ct_specimen_tree_file_decompressed.name)

    return SNOMED_CT_SPECIMEN_TYPE_DF


def get_specimen_label_from_specimen_code(specimen_code: int) -> str:
    """
    Given the specimen code, get the specimen label
    :param specimen_code:
    :return:
    """
    # Get the specimen tree
    specimen_tree_df = get_specimen_tree()

    # Query specimen code
    query_df = specimen_tree_df.query(
        f"Code=={specimen_code}"
    )

    # Assert that the query df is of length 1
    assert query_df.shape[0] == 1, f"Failed to get specimen code {specimen_code}"

    # Return the label
    return query_df['CodeLabel'].item()
