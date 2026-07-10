import { RemovalPolicy } from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3';
import { Construct } from 'constructs';
import { AddLookUpBucketProps } from './interfaces';
import { NagSuppressions } from 'cdk-nag';

export function addLookUpBucket(scope: Construct, props: AddLookUpBucketProps) {
  const s3Bucket = new s3.Bucket(scope, props.bucketName, {
    bucketName: props.bucketName,
    removalPolicy: RemovalPolicy.RETAIN_ON_UPDATE_OR_DELETE,
    enforceSSL: true,
  });

  // Add nag suppressions, while the bucket is not public,
  // It does not contain any private data
  NagSuppressions.addResourceSuppressions(
    s3Bucket,
    [
      {
        id: 'AwsSolutions-S1',
        reason:
          'Server access logs not required for the PierianDx lookup bucket; it contains only static SNOMED mapping reference data with no sensitive content',
      },
    ],
    true
  );

  return s3Bucket;
}
