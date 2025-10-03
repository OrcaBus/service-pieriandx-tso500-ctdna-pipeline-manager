#!/usr/bin/env python3

"""

Upload a file to pieriandx sample data s3 bucket

Given an icav2 uri, and a destination uri, download and upload the file into the destination uri

If needs_decompression is set to true, the downloaded file will be decompressed before uploading

Environment variables required are:
PIERIANDX_S3_ACCESS_CREDENTIALS_SECRET_ID -> The secret id for the s3 access credentials
ICAV2_ACCESS_TOKEN_SECRET_ID -> The secret id for the icav2 access token

Input will look like this

{
  "src_uri": "icav2://project-id/path/to/sample-microsat_output.txt",
  "dest_uri": "s3://pieriandx/melbourne/20201203_A00123_0001_BHJGJFDS__caseaccessionnumber__20240411235959/L2301368.microsat_output.json",
  "needs_decompression": false,
  "contents": null
}

"""

# Standard imports
from tempfile import TemporaryDirectory
from pathlib import Path
from urllib.parse import urlparse
import logging
import requests

# Layer imports
from orcabus_api_tools.filemanager import get_presigned_url, get_s3_object_id_from_s3_uri
from pieriandx_tools.aws_helpers.s3_helpers import upload_file
from pieriandx_tools.utils.compression_helpers import decompress_file

# Logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    """
    Upload pieriandx sample data to s3 bucket
    Args:
        event:
        context:

    Returns:

    """

    # Get uris
    needs_decompression = event.get("needsDecompression", False)
    dest_uri = event.get("destUri")
    dest_bucket = urlparse(dest_uri).netloc
    dest_key = urlparse(dest_uri).path
    src_uri = event.get("srcUri", None)
    contents = event.get("contents", None)

    if src_uri is not None:
        with TemporaryDirectory() as temp_dir:
            # Download the samplesheet to the temp file
            presigned_url = get_presigned_url(get_s3_object_id_from_s3_uri(src_uri))

            src_uri_obj = urlparse(src_uri)

            # Set output path
            output_path = Path(temp_dir) / Path(src_uri_obj.path).name

            if needs_decompression:
                with open(output_path, 'wb') as temp_file:
                    # Write the content to the temp file
                    temp_file.write(
                        requests.get(presigned_url).content
                    )

                decompress_file(output_path, output_path.parent / output_path.name.replace(".gz", ""))
                output_path = output_path.parent / output_path.name.replace(".gz", "")
            else:
                with open(output_path, 'w') as temp_file:
                    # Write the content to the temp file
                    temp_file.write(
                        requests.get(presigned_url).text
                    )

            # Hacky substitution to fix the incorrect header name in the MetricsOutput.tsv file
            if output_path.name.endswith("MetricsOutput.tsv"):
                with open(output_path, "r") as f:
                    contents = f.read()
                contents = contents.replace('[Run QC Metrics]', '[Run Metrics]')
                with open(output_path, "w") as f:
                    f.write(contents)

            # Upload to s3
            upload_file(dest_bucket, dest_key, output_path)
    else:
        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / Path(dest_key).name
            output_path.write_text(contents)

            upload_file(dest_bucket, dest_key, output_path)


if __name__ == "__main__":
    from os import environ
    environ["AWS_PROFILE"] = 'umccr-development'
    environ['AWS_REGION'] = 'ap-southeast-2'
    environ['HOSTNAME_SSM_PARAMETER_NAME'] = "/hosted_zone/umccr/name"
    environ['ORCABUS_TOKEN_SECRET_ID'] = "orcabus/token-service-jwt"
    environ['PIERIANDX_BASE_URL_SSM_PARAMETER_NAME'] = "/orcabus/workflows/pieriandx-tso500-ctdna/pieriandx-base-url"
    environ['PIERIANDX_COLLECT_AUTH_TOKEN_LAMBDA_NAME'] = "collectPierianDxAccessToken"
    environ['PIERIANDX_INSTITUTION_SSM_PARAMETER_NAME'] = "/orcabus/workflows/pieriandx-tso500-ctdna/pieriandx-institution"
    environ['PIERIANDX_S3_ACCESS_CREDENTIALS_SECRET_ID'] = "PierianDx/S3Credentials"
    environ['PIERIANDX_USER_EMAIL_SSM_PARAMETER_NAME'] = "/orcabus/workflows/pieriandx-tso500-ctdna/pieriandx-user-email"
    environ['PROJECT_INFO_DEFAULT_SSM_PARAMETER_NAME'] = "/orcabus/workflows/pieriandx-tso500-ctdna/default-project-info"
    environ['PROJECT_INFO_SSM_PARAMETER_PREFIX'] = "/orcabus/workflows/pieriandx-tso500-ctdna/project-info-by-project-type-map"

    handler(
        {
            "srcUri": "s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/dragen-tso500-ctdna/202509120afc2e2a/Results/L2500384/L2500384.cnv.vcf.gz",
            "needsDecompression": True,
            "destUri": "s3://pdx-cgwxfer-test/melbournetest/250328_A01052_0258_AHFGM7DSXF__L2500384_004/Data/Intensities/BaseCalls/L2500384.cnv.vcf"
        },
        None
    )

# if __name__ == "__main__":
#     from os import environ
#     environ["AWS_PROFILE"] = 'umccr-production'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ["ICAV2_ACCESS_TOKEN_SECRET_ID"] = "ICAv2JWTKey-umccr-prod-service-production"
#     environ['PIERIANDX_S3_ACCESS_CREDENTIALS_SECRET_ID'] = "PierianDx/S3Credentials"
#
#     handler(
#         {
#           "needs_decompression": False,
#           "src_uri": "s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/analysis/cttsov2/202411053da6481e/Results/L2401560/L2401560_MetricsOutput.tsv",
#           "contents": None,
#           "dest_uri": "s3://pdx-xfer/melbourne/241101_A01052_0236_BHVJNMDMXY__L2401560__V2__20241105f6bc3fb9__20241105f6bc3fb9/Data/Intensities/BaseCalls/L2401560_MetricsOutput.tsv"
#         },
#         None
#     )
#
