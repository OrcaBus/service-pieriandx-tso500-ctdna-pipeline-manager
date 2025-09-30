#!/usr/bin/env python

"""
Download file from s3
"""

# Standard Imports
import typing
from pathlib import Path
import boto3


if typing.TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client


def get_pieriandx_s3_client() -> 'S3Client':
    from ..pieriandx_helpers import get_pieriandx_s3_access_credentials
    return boto3.client(
        's3',
        aws_access_key_id=get_pieriandx_s3_access_credentials()['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=get_pieriandx_s3_access_credentials()['AWS_SECRET_ACCESS_KEY']
    )


def upload_file(bucket: str, key: str, input_file_path: Path) -> None:
    s3 = get_pieriandx_s3_client()
    s3.upload_file(
        str(input_file_path),
        bucket,
        key.lstrip("/"),
        ExtraArgs={
            'ServerSideEncryption': 'AES256'
        }
    )


def get_s3_client() -> 'S3Client':
    return boto3.client('s3')


def download_file(
        bucket: str,
        key: str,
        output_file_path: Path
):
    get_s3_client().download_file(
        Bucket=bucket,
        Key=key.lstrip("/"),
        Filename=str(output_file_path)
    )
