/** Step Function stuff */
import {
  BuildStepFunctionProps,
  BuildStepFunctionsProps,
  stateMachineNameList,
  StepFunctionObject,
  stepFunctionsRequirementsMap,
  stepFunctionToLambdasMap,
  WireUpPermissionsProps,
} from './interfaces';
import { NagSuppressions } from 'cdk-nag';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as cdk from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import path from 'path';
import {
  DEFAULT_PAYLOAD_VERSION,
  DRAFT_STATUS,
  EVENT_SOURCE,
  READY_STATUS,
  SUCCEEDED_STATUS,
  DRAGEN_TSO500_CTDNA_WORKFLOW_NAME,
  STACK_PREFIX,
  STEP_FUNCTIONS_DIR,
  WORKFLOW_NAME,
  WORKFLOW_RUN_STATE_CHANGE_DETAIL_TYPE,
  WORKFLOW_RUN_UPDATE_DETAIL_TYPE,
  MONITOR_EVENT_RULE_NAME,
  RUNNABLE_STATUS,
} from '../constants';
import { Construct } from 'constructs';
import { camelCaseToSnakeCase } from '../utils';

function createStateMachineDefinitionSubstitutions(props: BuildStepFunctionProps): {
  [key: string]: string;
} {
  const definitionSubstitutions: { [key: string]: string } = {};

  const sfnRequirements = stepFunctionsRequirementsMap[props.stateMachineName];
  const lambdaFunctionNamesInSfn = stepFunctionToLambdasMap[props.stateMachineName];
  const lambdaFunctions = props.lambdaObjects.filter((lambdaObject) =>
    lambdaFunctionNamesInSfn.includes(lambdaObject.lambdaName)
  );

  /* Substitute lambdas in the state machine definition */
  for (const lambdaObject of lambdaFunctions) {
    const sfnSubtitutionKey = `__${camelCaseToSnakeCase(lambdaObject.lambdaName)}_lambda_function_arn__`;
    definitionSubstitutions[sfnSubtitutionKey] =
      lambdaObject.lambdaFunction.currentVersion.functionArn;
  }

  /* Common substitutions */
  // Status
  definitionSubstitutions['__draft_status__'] = DRAFT_STATUS;
  definitionSubstitutions['__ready_status__'] = READY_STATUS;
  definitionSubstitutions['__succeeded_status__'] = SUCCEEDED_STATUS;
  definitionSubstitutions['__runnable_status__'] = RUNNABLE_STATUS;
  // Oncoanalyser workflow names
  definitionSubstitutions['__dragen_tso500_ctdna_workflow_name__'] =
    DRAGEN_TSO500_CTDNA_WORKFLOW_NAME;
  definitionSubstitutions['__default_payload_version__'] = DEFAULT_PAYLOAD_VERSION;
  // Stack workflow name
  definitionSubstitutions['__workflow_name__'] = WORKFLOW_NAME;

  /* Sfn Requirements */
  if (sfnRequirements.needsEventPutPermission) {
    definitionSubstitutions['__event_bus_name__'] = props.eventBus.eventBusName;
    definitionSubstitutions['__workflow_run_state_change_event_detail_type__'] =
      WORKFLOW_RUN_STATE_CHANGE_DETAIL_TYPE;
    definitionSubstitutions['__workflow_run_update_event_detail_type__'] =
      WORKFLOW_RUN_UPDATE_DETAIL_TYPE;
    definitionSubstitutions['__stack_source__'] = EVENT_SOURCE;
    definitionSubstitutions['__ready_event_status__'] = READY_STATUS;
    definitionSubstitutions['__new_workflow_manager_is_deployed__'] =
      props.isNewWorkflowManagerDeployed.toString();
  }

  if (sfnRequirements.needsSsmParameterStoreAccess) {
    // Default parameter paths
    definitionSubstitutions['__workflow_name_ssm_parameter_name__'] =
      props.ssmParameterPaths.workflowName; // Not currently used

    // SSM Prefixes

    // DAG
    definitionSubstitutions['__dag_version_ssm_parameter_prefix__'] =
      props.ssmParameterPaths.dagNameByDagVersionPrefix;
    definitionSubstitutions['__dag_version_default_ssm_parameter_path__'] =
      props.ssmParameterPaths.defaultDagVersionPath;

    // Panel
    definitionSubstitutions['__panel_name_ssm_parameter_prefix__'] =
      props.ssmParameterPaths.panelIdByPanelNamePrefix;
    definitionSubstitutions['__panel_name_default_ssm_parameter_path__'] =
      props.ssmParameterPaths.defaultPanelNamePath;

    // Sequencer s3 path
    definitionSubstitutions['__sequencerrun_s3_path_ssm_parameter__'] =
      props.ssmParameterPaths.sequencerrunRoot;
  }

  if (sfnRequirements.needsEventRulePermissions) {
    definitionSubstitutions['__scheduler_rule_name__'] =
      `${STACK_PREFIX}-${MONITOR_EVENT_RULE_NAME}`;
  }

  return definitionSubstitutions;
}

function wireUpStateMachinePermissions(props: WireUpPermissionsProps): void {
  /* Wire up lambda permissions */
  const sfnRequirements = stepFunctionsRequirementsMap[props.stateMachineName];

  const lambdaFunctionNamesInSfn = stepFunctionToLambdasMap[props.stateMachineName];
  const lambdaFunctions = props.lambdaObjects.filter((lambdaObject) =>
    lambdaFunctionNamesInSfn.includes(lambdaObject.lambdaName)
  );

  /* Allow the state machine to invoke the lambda function */
  for (const lambdaObject of lambdaFunctions) {
    lambdaObject.lambdaFunction.currentVersion.grantInvoke(props.sfnObject);
  }

  // Needs Event put permissions
  if (sfnRequirements.needsEventPutPermission) {
    props.eventBus.grantPutEventsTo(props.sfnObject);
  }

  // Needs SSM Parameter Store access
  if (sfnRequirements.needsSsmParameterStoreAccess) {
    // We give access to the full prefix
    // At the cost of needing a nag suppression
    props.sfnObject.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ['ssm:GetParameter'],
        resources: [
          `arn:aws:ssm:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:parameter${path.join(props.ssmParameterPaths.ssmRootPrefix, '/*')}`,
        ],
      })
    );

    NagSuppressions.addResourceSuppressions(
      props.sfnObject,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason: 'We need to give access to the full prefix for the SSM parameter store',
        },
      ],
      true
    );
  }

  // Needs event rule permissions
  if (sfnRequirements.needsEventRulePermissions) {
    props.sfnObject.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ['events:EnableRule', 'events:DisableRule'],
        resources: [
          `arn:aws:events:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:rule/${STACK_PREFIX}-${MONITOR_EVENT_RULE_NAME}`,
        ],
      })
    );
  }
}

function buildStepFunction(scope: Construct, props: BuildStepFunctionProps): StepFunctionObject {
  const sfnNameToSnakeCase = camelCaseToSnakeCase(props.stateMachineName);

  /* Create the state machine definition substitutions */
  const stateMachine = new sfn.StateMachine(scope, props.stateMachineName, {
    stateMachineName: `${STACK_PREFIX}-${props.stateMachineName}`,
    definitionBody: sfn.DefinitionBody.fromFile(
      path.join(STEP_FUNCTIONS_DIR, sfnNameToSnakeCase + `_sfn_template.asl.json`)
    ),
    definitionSubstitutions: createStateMachineDefinitionSubstitutions(props),
  });

  /* Grant the state machine permissions */
  wireUpStateMachinePermissions({
    sfnObject: stateMachine,
    ...props,
  });

  /* Nag Suppressions */
  /* AwsSolutions-SF1 - We don't need ALL events to be logged */
  /* AwsSolutions-SF2 - We also don't need X-Ray tracing */
  NagSuppressions.addResourceSuppressions(
    stateMachine,
    [
      {
        id: 'AwsSolutions-SF1',
        reason: 'We do not need all events to be logged',
      },
      {
        id: 'AwsSolutions-SF2',
        reason: 'We do not need X-Ray tracing',
      },
    ],
    true
  );

  /* Return as a state machine object property */
  return {
    ...props,
    sfnObject: stateMachine,
  };
}

export function buildAllStepFunctions(
  scope: Construct,
  props: BuildStepFunctionsProps
): StepFunctionObject[] {
  const stepFunctionObjects: StepFunctionObject[] = [];

  for (const stepFunctionName of stateMachineNameList) {
    stepFunctionObjects.push(
      buildStepFunction(scope, {
        stateMachineName: stepFunctionName,
        lambdaObjects: props.lambdaObjects,
        eventBus: props.eventBus,
        isNewWorkflowManagerDeployed: props.isNewWorkflowManagerDeployed,
        ssmParameterPaths: props.ssmParameterPaths,
      })
    );
  }

  return stepFunctionObjects;
}
