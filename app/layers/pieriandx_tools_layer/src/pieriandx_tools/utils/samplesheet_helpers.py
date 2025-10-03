#!/usr/bin/env python

# Standard imports
from typing import Dict
from pathlib import Path
from tempfile import NamedTemporaryFile
import requests

# Layer imports
from orcabus_api_tools.filemanager import get_presigned_url, get_s3_object_id_from_s3_uri

# Custom imports
from v2_samplesheet_maker.functions.v2_samplesheet_reader import v2_samplesheet_reader


def read_v2_samplesheet(samplesheet_uri: str) -> Dict:
    """
    Read in a v2 samplesheet from the given uri and return as a dictionary

    Args:
        samplesheet_uri: Path to the samplesheet s3 or icav2 uri

    Returns:

    """

    # Download the samplesheet to the temp file
    presigned_url = get_presigned_url(get_s3_object_id_from_s3_uri(samplesheet_uri))

    with NamedTemporaryFile(suffix=".csv") as temp_file:
        # Write the content to the temp file
        temp_file.write(
            requests.get(presigned_url).content
        )
        # Ensure the content is written to disk
        temp_file.flush()

        # Move the file pointer to the beginning of the file
        temp_file.seek(0)

        # Read the v2 samplesheet from the temp file
        return v2_samplesheet_reader(
            Path(temp_file.name)
        )
