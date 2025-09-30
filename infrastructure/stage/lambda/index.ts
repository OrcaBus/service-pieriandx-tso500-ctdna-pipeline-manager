import {
  BuildLambdaInput,
  BuildLambdasInput,
  lambdaNameList,
  LambdaObject,
  lambdaRequirementsMap,
} from './interfaces';
import { PythonUvFunction } from '@orcabus/platform-cdk-constructs/lambda';
import { LAMBDA_DIR, SCHEMA_REGISTRY_NAME, SSM_SCHEMA_ROOT } from '../constants';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { Duration } from 'aws-cdk-lib';
import { NagSuppressions } from 'cdk-nag';
import { Construct } from 'constructs';
import { camelCaseToKebabCase, camelCaseToSnakeCase } from '../utils';
import * as path from 'path';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as cdk from 'aws-cdk-lib';
import { SchemaNames } from '../event-schemas/interfaces';

function buildLambda(scope: Construct, props: BuildLambdaInput): LambdaObject {
  const lambdaNameToSnakeCase = camelCaseToSnakeCase(props.lambdaName);
  const lambdaRequirements = lambdaRequirementsMap[props.lambdaName];

  // Create the lambda function
  const lambdaFunction = new PythonUvFunction(scope, props.lambdaName, {
    entry: path.join(LAMBDA_DIR, lambdaNameToSnakeCase + '_py'),
    runtime: lambda.Runtime.PYTHON_3_12,
    architecture: lambda.Architecture.ARM_64,
    index: lambdaNameToSnakeCase + '.py',
    handler: 'handler',
    timeout: Duration.seconds(60),
    memorySize: 2048,
    includeOrcabusApiToolsLayer: lambdaRequirements.needsOrcabusApiTools,
  });

  // AwsSolutions-L1 - We'll migrate to PYTHON_3_13 ASAP, soz
  // AwsSolutions-IAM4 - We need to add this for the lambda to work
  NagSuppressions.addResourceSuppressions(
    lambdaFunction,
    [
      {
        id: 'AwsSolutions-L1',
        reason: 'Will migrate to PYTHON_3_13 ASAP, soz',
      },
      {
        id: 'AwsSolutions-IAM4',
        reason: 'We use the basic execution role for lambda functions',
      },
    ],
    true
  );

  /*
    Add in SSM permissions for the lambda function
    */
  if (lambdaRequirements.needsSsmParametersAccess || lambdaRequirements.needsPieriandxLayerAccess) {
    lambdaFunction.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ['ssm:GetParameter'],
        resources: [
          `arn:aws:ssm:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:parameter${path.join(props.ssmParameterNames.ssmRootPrefix, '/*')}`,
        ],
      })
    );
    /* As such we need to add the wildcard to the resource */
    NagSuppressions.addResourceSuppressions(
      lambdaFunction,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason: 'We need to give the lambda access to ssm parameters under the prefix',
        },
      ],
      true
    );

    // Project Info
    lambdaFunction.addEnvironment(
      'PROJECT_INFO_SSM_PARAMETER_PREFIX',
      props.ssmParameterNames.projectInfoConfigurationMapPrefix
    );
    lambdaFunction.addEnvironment(
      'PROJECT_INFO_DEFAULT_SSM_PARAMETER_NAME',
      props.ssmParameterNames.defaultProjectInfoConfigurationPath
    );
  }

  /*
  Needs PierianDx Layer access (add in layer)
   */
  if (lambdaRequirements.needsPieriandxLayerAccess) {
    // Add in the PierianDx Layer
    lambdaFunction.addLayers(props.pieriandxLambdaLayer);

    // Give lambda permission to invoke the auth token lambda
    props.authTokenLambdaFunction.grantInvoke(lambdaFunction.currentVersion);

    // Give lambda permission to read the S3 credentials secret
    props.s3CredentialsSecret.grantRead(lambdaFunction.currentVersion);

    // Give lambda permission to read the S3 lookup bucket
    props.s3LookUpBucket.grantRead(lambdaFunction.currentVersion);

    // And add in all the required environment variables
    lambdaFunction.addEnvironment(
      'PIERIANDX_USER_EMAIL_SSM_PARAMETER_NAME',
      props.ssmParameterNames.pierianDxUserEmail
    );
    lambdaFunction.addEnvironment(
      'PIERIANDX_INSTITUTION_SSM_PARAMETER_NAME',
      props.ssmParameterNames.pierianDxInstitution
    );
    lambdaFunction.addEnvironment(
      'PIERIANDX_BASE_URL_SSM_PARAMETER_NAME',
      props.ssmParameterNames.pierianDxBaseUrl
    );
    lambdaFunction.addEnvironment(
      'PIERIANDX_COLLECT_AUTH_TOKEN_LAMBDA_NAME',
      props.authTokenLambdaFunction.functionName
    );
    lambdaFunction.addEnvironment(
      'PIERIANDX_S3_ACCESS_CREDENTIALS_SECRET_ID',
      props.s3CredentialsSecret.secretName
    );

    // S3
    lambdaFunction.addEnvironment(
      'SNOMED_CT_SPECIMEN_TYPE_SSM_PARAMETER_NAME',
      props.ssmParameterNames.snomedSpecimenTypeS3Path
    );
    lambdaFunction.addEnvironment(
      'SNOMED_CT_DISEASE_TREE_S3_PATH_SSM_PARAMETER_NAME',
      props.ssmParameterNames.snomedCtDiseaseTreeS3Path
    );

    /* As such we need to add the wildcard to the resource */
    NagSuppressions.addResourceSuppressions(
      lambdaFunction,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason: 'We need to give the lambda access to the s3 bucket which results in a wildcard',
        },
      ],
      true
    );
  }

  if (lambdaRequirements.needsRedcapLambdaPermission) {
    // Give lambda permission to invoke the auth token lambda
    props.redcapLambdaFunction.grantInvoke(lambdaFunction.currentVersion);
    lambdaFunction.addEnvironment(
      'REDCAP_LAMBDA_FUNCTION_NAME',
      props.redcapLambdaFunction.functionName
    );

    /* We dont have control over the redcap lambda, so we allow our lambda to run any version */
    /* As such we need to add the wildcard to the resource */
    NagSuppressions.addResourceSuppressions(
      lambdaFunction,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason: 'Allow redcap lambda to be invoked on any version',
        },
      ],
      true
    );
  }

  /*
    For the schema validation lambdas we need to give them the access to the schema
    */
  if (lambdaRequirements.needsSchemaRegistryAccess) {
    // Add the schema registry access to the lambda function
    lambdaFunction.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ['schemas:DescribeRegistry', 'schemas:DescribeSchema'],
        resources: [
          `arn:aws:schemas:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:registry/${SCHEMA_REGISTRY_NAME}`,
          `arn:aws:schemas:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:schema/${path.join(SCHEMA_REGISTRY_NAME, '/*')}`,
        ],
      })
    );

    /* Since we dont ask which schema, we give the lambda access to all schemas in the registry */
    /* As such we need to add the wildcard to the resource */
    NagSuppressions.addResourceSuppressions(
      lambdaFunction,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason: 'We need to give the lambda access to all schemas in the registry',
        },
      ],
      true
    );
  }

  /*
    Special if the lambdaName is 'validateDraftCompleteSchema', we need to add in the ssm parameters
    to the REGISTRY_NAME and SCHEMA_NAME
   */
  if (props.lambdaName === 'validateDraftDataCompleteSchema') {
    const draftSchemaName: SchemaNames = 'completeDataDraft';
    lambdaFunction.addEnvironment('SSM_REGISTRY_NAME', path.join(SSM_SCHEMA_ROOT, 'registry'));
    lambdaFunction.addEnvironment(
      'SSM_SCHEMA_NAME',
      path.join(SSM_SCHEMA_ROOT, camelCaseToKebabCase(draftSchemaName), 'latest')
    );
  }

  /* Return the function */
  return {
    lambdaName: props.lambdaName,
    lambdaFunction: lambdaFunction,
  };
}

export function buildAllLambdas(scope: Construct, props: BuildLambdasInput): LambdaObject[] {
  // Iterate over lambdaLayerToMapping and create the lambda functions
  const lambdaObjects: LambdaObject[] = [];
  for (const lambdaName of lambdaNameList) {
    lambdaObjects.push(
      buildLambda(scope, {
        lambdaName: lambdaName,
        ...props,
      })
    );
  }

  return lambdaObjects;
}
