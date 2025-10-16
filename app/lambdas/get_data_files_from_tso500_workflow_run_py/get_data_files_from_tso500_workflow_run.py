#!/usr/bin/env python3

"""
Given a TSO500 workflow portal run id,

1. Get the latest (SUCCEEDED) payload.
2. Get all the files in the output directory that match the pattern needed
3. Return the file paths as an object

Given the output uri, get the data files ready to upload into the pieriandx s3 bucket

So given the output uri
's3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/'
And a sample id
'L2400161'

We would expect the following files to be returned:
{
    "microsatOutputUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Logs_Intermediates/DragenCaller/L2400161/L2400161.microsat_output.json",
    "tmbMetricsUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Logs_Intermediates/Tmb/L2400161/L2400161.tmb.metrics.csv",
    "cnvVcfUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Results/L2400161/L2400161.cnv.vcf.gz",
    "hardFilteredVcfUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Results/L2400161/L2400161.hard-filtered.vcf.gz",
    "fusionsUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Results/L2400161/L2400161_Fusions.csv",
    "metricsOutputUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Results/L2400161/L2400161_MetricsOutput.tsv",
    "samplesheetUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/cttsov2/20240910d260200d/Logs_Intermediates/SampleSheetValidation/SampleSheet_Intermediate.csv"
}
"""

# Standard imports
import logging

# Typing imports
from typing import Dict, Literal, List
from urllib.parse import urlunparse

# Layered imports
from orcabus_api_tools.filemanager import list_files_from_portal_run_id
from orcabus_api_tools.filemanager.models import FileObject
from orcabus_api_tools.workflow import get_latest_payload_from_portal_run_id

# Globals / Type hints
OutputKeysType = Literal[
    "microsatOutputUri",
    "geneCovReportUri",
    "exonCovReportUri",
    "tmbMetricsUri",
    "cnvVcfUri",
    "hardFilteredVcfUri",
    "fusionsUri",
    "metricsOutputUri",
    "samplesheetUri",
]

OUTPUT_KEYS_LIST: List[OutputKeysType] = [
    "microsatOutputUri",
    "geneCovReportUri",
    "exonCovReportUri",
    "tmbMetricsUri",
    "cnvVcfUri",
    "hardFilteredVcfUri",
    "fusionsUri",
    "metricsOutputUri",
    "samplesheetUri",
]

URL_EXTENSION_MAP: Dict[OutputKeysType, str] = {
    "microsatOutputUri": "Logs_Intermediates/DragenCaller/{SAMPLE_ID}/{SAMPLE_ID}.microsat_output.json",
    "geneCovReportUri": "Results/{SAMPLE_ID}/{SAMPLE_ID}.gene_cov_report.tsv",
    "exonCovReportUri": "Results/{SAMPLE_ID}/{SAMPLE_ID}.exon_cov_report.tsv",
    "tmbMetricsUri": "Logs_Intermediates/Tmb/{SAMPLE_ID}/{SAMPLE_ID}.tmb.metrics.csv",
    "cnvVcfUri": "Results/{SAMPLE_ID}/{SAMPLE_ID}.cnv.vcf.gz",
    "hardFilteredVcfUri": "Results/{SAMPLE_ID}/{SAMPLE_ID}.hard-filtered.vcf.gz",
    "fusionsUri": "Results/{SAMPLE_ID}/{SAMPLE_ID}_Fusions.csv",
    "metricsOutputUri": "Results/{SAMPLE_ID}/{SAMPLE_ID}_MetricsOutput.tsv",
    "samplesheetUri": "Logs_Intermediates/SampleSheetValidation/SampleSheet_Intermediate.csv",
}

# Set loggers
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_data_file_output_uri(
    data_file_key: OutputKeysType,
    sample_id: str,
    output_tso500_data: List[FileObject]
) -> str:
    file_obj = next(filter(
        lambda file_iter_: file_iter_['key'].endswith(
            URL_EXTENSION_MAP[data_file_key].format(
                **dict({
                    "SAMPLE_ID": sample_id
                })
            )
        ),
        output_tso500_data
    ))

    return str(urlunparse((
        "s3",
        file_obj['bucket'],
        file_obj['key'],
        None, None, None
    )))


def handler(event, context) -> Dict[str, Dict[str, str]]:
    """
    Firse we need to set the icav2 env vars
    :param event:
    :param context:
    :return:
    """
    # Portal run id
    portal_run_id = event.get("portalRunId")

    # Get the latest payload
    sample_id = get_latest_payload_from_portal_run_id(portal_run_id)['data']['inputs']['sampleName']

    # List output files
    output_tso500_data = list_files_from_portal_run_id(portal_run_id)

    data_files = dict(map(
        lambda data_file_key_iter_: (
            data_file_key_iter_,
            get_data_file_output_uri(
                data_file_key=data_file_key_iter_,
                sample_id=sample_id,
                output_tso500_data=output_tso500_data
            )
        ),
        OUTPUT_KEYS_LIST
    ))

    return {
        "dataFiles": data_files
    }
