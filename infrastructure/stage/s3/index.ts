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
  // AwsSolutions-S1 - We need to add this for the lambda to work
  NagSuppressions.addResourceSuppressions(
    s3Bucket,
    [
      {
        id: 'AwsSolutions-S1',
        reason: 'We dont need server access logs for this bucket',
      },
    ],
    true
  );

  return s3Bucket;
}
