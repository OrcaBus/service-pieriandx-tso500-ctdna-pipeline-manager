import * as cdk from 'aws-cdk-lib';
import * as events from 'aws-cdk-lib/aws-events';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import * as s3 from 'aws-cdk-lib/aws-s3';
import { Construct } from 'constructs';
import { StatelessApplicationStackConfig } from './interfaces';
import { buildAllLambdas } from './lambda';
import { buildAllStepFunctions } from './step-functions';
import { buildAllEventRules } from './event-rules';
import { buildAllEventBridgeTargets } from './event-targets';
import {
  PIERIANDX_COLLECT_AUTH_TOKEN_LAMBDA_NAME,
  PIERIANDX_S3_CREDENTIALS_SECRET_NAME,
} from './constants';
import { buildPierianDxToolsLayer } from './layers';

export type StatelessApplicationStackProps = cdk.StackProps & StatelessApplicationStackConfig;

export class StatelessApplicationStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: StatelessApplicationStackProps) {
    super(scope, id, props);

    /**
     * PierianDx Stack
     * Deploys the PierianDx orchestration services
     */
    // Get the event bus as a construct
    const orcabusMainEventBus = events.EventBus.fromEventBusName(
      this,
      props.eventBusName,
      props.eventBusName
    );

    // Build the pieriandx lambda layer
    const pieriandxLambdaLayer = buildPierianDxToolsLayer(this);

    // Get the external lambda functions
    const pieriandxAuthLambdaFunction = lambda.Function.fromFunctionName(
      this,
      'PierianDxAuthLambdaFunction',
      PIERIANDX_COLLECT_AUTH_TOKEN_LAMBDA_NAME
    );
    const redcapLambdaFunction = lambda.Function.fromFunctionName(
      this,
      'RedcapLambdaFunction',
      props.redcapLambdaName
    );

    // Get the external secrets
    const s3CredentialsSecret = secretsManager.Secret.fromSecretNameV2(
      this,
      'PierianDxS3CredentialsSecret',
      PIERIANDX_S3_CREDENTIALS_SECRET_NAME
    );

    // Get the s3 bucket
    const s3LookUpBucket = s3.Bucket.fromBucketName(this, 'S3LookUpBucket', props.lookupBucketName);

    // Build the lambdas
    const lambdas = buildAllLambdas(this, {
      // PierianDx Lambda layer
      pieriandxLambdaLayer: pieriandxLambdaLayer,

      // SSM
      ssmParameterNames: props.ssmParameterPaths,

      // authTokenLambdaFunction
      authTokenLambdaFunction: pieriandxAuthLambdaFunction,

      // redcapLambdaFunction
      redcapLambdaFunction: redcapLambdaFunction,

      // s3CredentialsSecret
      s3CredentialsSecret: s3CredentialsSecret,

      // s3LookUpBucket
      s3LookUpBucket: s3LookUpBucket,
    });

    // Build the state machines
    const stateMachines = buildAllStepFunctions(this, {
      lambdaObjects: lambdas,
      eventBus: orcabusMainEventBus,
      isNewWorkflowManagerDeployed: props.isNewWorkflowManagerDeployed,
      ssmParameterPaths: props.ssmParameterPaths,
    });

    // Add event rules
    const eventRules = buildAllEventRules(this, {
      eventBus: orcabusMainEventBus,
    });

    // Add event targets
    buildAllEventBridgeTargets({
      eventBridgeRuleObjects: eventRules,
      stepFunctionObjects: stateMachines,
    });
  }
}
