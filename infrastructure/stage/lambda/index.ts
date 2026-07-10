import {
  BuildLambdaInput,
  BuildLambdasInput,
  lambdaNameList,
  LambdaObject,
  lambdaRequirementsMap,
} from './interfaces';
import { PythonUvFunction } from '@orcabus/platform-cdk-constructs/lambda';
import {
  LAMBDA_DIR,
  SCHEMA_REGISTRY_NAME,
  SSM_SCHEMA_ROOT,
  WORKFLOW_NAME,
  DEFAULT_PAYLOAD_VERSION,
} from '../constants';
import { REPO_NAME } from '../../toolchain/constants';
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
    runtime: lambda.Runtime.PYTHON_3_14,
    architecture: lambda.Architecture.ARM_64,
    index: lambdaNameToSnakeCase + '.py',
    handler: 'handler',
    timeout: lambdaRequirements.needsExtendedTimeout ? Duration.seconds(900) : Duration.seconds(60),
    memorySize:
      lambdaRequirements.needsPieriandxLayerAccess || lambdaRequirements.needsHigherMemory
        ? 1024
        : 512,
    includeOrcabusApiToolsLayer: lambdaRequirements.needsOrcabusApiTools,
  });

  // AwsSolutions-L1 - Python 3.14 is not yet in the cdk-nag approved list but is our target runtime
  // AwsSolutions-IAM4 - Basic execution role provides CloudWatch Logs permissions needed by all Lambdas
  NagSuppressions.addResourceSuppressions(
    lambdaFunction,
    [
      {
        id: 'AwsSolutions-L1',
        reason:
          'Python 3.14 is not yet in the cdk-nag approved list but is our target runtime for ARM64 Lambda functions',
      },
      {
        id: 'AwsSolutions-IAM4',
        reason:
          'Basic execution managed policy provides CloudWatch Logs permissions required by all Lambda functions',
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
    NagSuppressions.addResourceSuppressions(
      lambdaFunction,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason:
            'Wildcard covers SSM parameters under the workflow root path; specific parameter names include versions and project types determined at runtime',
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
    props.authTokenLambdaFunction.grantInvoke(lambdaFunction);

    // Give lambda permission to read the S3 credentials secret
    props.s3CredentialsSecret.grantRead(lambdaFunction);

    // Give lambda permission to read the S3 lookup bucket
    props.s3LookUpBucket.grantRead(lambdaFunction);

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
          reason:
            'Wildcard covers S3 objects in the PierianDx lookup bucket; individual object ARNs cannot be enumerated at deploy time because SNOMED mapping files are versioned dynamically',
        },
      ],
      true
    );
  }

  if (lambdaRequirements.needsRedcapLambdaPermission) {
    // Give lambda permission to invoke the auth token lambda
    props.redcapLambdaFunction.grantInvoke(lambdaFunction);
    lambdaFunction.addEnvironment(
      'REDCAP_LAMBDA_FUNCTION_NAME',
      props.redcapLambdaFunction.functionName
    );

    /* We dont have control over the redcap lambda, so we allow our lambda to run any version */
    NagSuppressions.addResourceSuppressions(
      lambdaFunction,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason:
            'Wildcard covers all versions of the RedCap Lambda function; version-specific ARNs cannot be enumerated because the RedCap Lambda is managed externally',
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
    NagSuppressions.addResourceSuppressions(
      lambdaFunction,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason:
            'Wildcard covers all schema versions in the registry; individual schema ARNs cannot be enumerated at deploy time because versions are created dynamically',
        },
      ],
      true
    );
  }

  /*
    For Lambdas that need schema registry access,
    we need to add in the ssm parameters for REGISTRY_NAME and SCHEMA_PATH
   */
  if (lambdaRequirements.needsSchemaRegistryAccess) {
    const draftSchemaName: SchemaNames = 'completeDataDraft';
    lambdaFunction.addEnvironment('SSM_REGISTRY_NAME', path.join(SSM_SCHEMA_ROOT, 'registry'));
    lambdaFunction.addEnvironment(
      'SSM_SCHEMA_PATH',
      path.join(SSM_SCHEMA_ROOT, camelCaseToKebabCase(draftSchemaName))
    );
    lambdaFunction.addEnvironment('DEFAULT_PAYLOAD_VERSION', DEFAULT_PAYLOAD_VERSION);
  }

  /*
    Workflow info, usually for comment generation on the workflow run in the OrcaUI
   */
  if (lambdaRequirements.needsWorkflowInfo) {
    lambdaFunction.addEnvironment('WORKFLOW_NAME', WORKFLOW_NAME);
  }

  /*
    Repository GitHub URL, used in user-facing comments to link to the README
   */
  if (lambdaRequirements.needsRepoUrl) {
    lambdaFunction.addEnvironment(
      'REPOSITORY_GITHUB_URL',
      `https://github.com/OrcaBus/${REPO_NAME}`
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

export function getLambdaResourceLogicalArn(lambdaFunction: lambda.Function): string | null {
  // Find L1 CloudFormation CfnFunction resource(s) under the L2 Function (exclude Alias/Version L1s)
  const cfnFunctions = lambdaFunction.node
    .findAll()
    .filter((n) => n instanceof lambda.CfnFunction) as lambda.CfnFunction[];

  // Use the first CfnFunction's logical ID
  if (cfnFunctions.length > 0) {
    const logicalId = cdk.Stack.of(lambdaFunction).getLogicalId(cfnFunctions[0]);
    return `Resource::<${logicalId}.Arn>:*`;
  }

  return null;
}
