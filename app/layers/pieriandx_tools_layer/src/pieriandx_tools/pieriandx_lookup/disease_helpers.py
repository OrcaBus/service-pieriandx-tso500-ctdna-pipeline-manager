#!/usr/bin/env python3

"""
Given a disease code, get the disease label
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
# https://velserapm.atlassian.net/wiki/download/attachments/86704490/SNOMED_CT%20Disease_trees.xlsx?version=1&modificationDate=1561395438000&api=v2
SNOMED_CT_DISEASE_TREE_S3_PATH_SSM_ENV_VAR = "SNOMED_CT_DISEASE_TREE_S3_PATH_SSM_PARAMETER_NAME"
SNOMED_CT_DISEASE_TREE_DF = None


def get_disease_tree() -> pd.DataFrame:
    """
    Returns a dataframe with the following columns
    * Code
    * CodeSystem
    * Label
    :return:
    """
    from ..aws_helpers.s3_helpers import download_file

    global SNOMED_CT_DISEASE_TREE_DF

    if SNOMED_CT_DISEASE_TREE_DF is not None:
        return SNOMED_CT_DISEASE_TREE_DF

    # Download the file from S3
    with (
        NamedTemporaryFile(suffix='json.gz') as snomed_ct_disease_tree_file_compressed,
        NamedTemporaryFile(suffix='json') as snomed_ct_disease_tree_file_decompressed,
    ):
        # Get the s3 uri path
        s3_obj = urlparse(get_ssm_value(environ[SNOMED_CT_DISEASE_TREE_S3_PATH_SSM_ENV_VAR]))

        # Download the file from S3
        download_file(
            bucket=s3_obj.netloc,
            key=s3_obj.path.lstrip('/'),
            output_file_path=Path(snomed_ct_disease_tree_file_compressed.name)
        )

        # Flush to ensure all data is written
        snomed_ct_disease_tree_file_compressed.flush()

        # Decompress the file
        decompress_file(
            Path(snomed_ct_disease_tree_file_compressed.name),
            Path(snomed_ct_disease_tree_file_decompressed.name)
        )

        # Flush to ensure all data is written
        snomed_ct_disease_tree_file_decompressed.flush()

        # Read the decompressed file into a dataframe
        SNOMED_CT_DISEASE_TREE_DF = pd.read_json(snomed_ct_disease_tree_file_decompressed.name)

    return SNOMED_CT_DISEASE_TREE_DF


def get_disease_label_from_disease_code(disease_code: int) -> str:
    """
    Given the disease code, get the disease label
    :param disease_code:
    :return:
    """

    # Get the disease tree
    disease_tree_df = get_disease_tree()

    # Query disease code
    query_df = disease_tree_df.query(
        f"Code=={disease_code}"
    )

    # Assert that the query df is of length 1
    assert query_df.shape[0] == 1, f"Failed to get disease code {disease_code}"

    # Return the label
    return query_df['Label'].item()
