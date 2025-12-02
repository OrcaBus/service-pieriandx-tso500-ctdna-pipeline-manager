import { IEventBus } from 'aws-cdk-lib/aws-events';
import { StateMachine } from 'aws-cdk-lib/aws-stepfunctions';

import { LambdaName, LambdaObject } from '../lambda/interfaces';
import { SsmParameterPaths } from '../ssm/interfaces';

/**
 * Step Function Interfaces
 */
export type StateMachineName =
  // Glue code
  | 'glueSucceededEventsToDraftUpdate'
  // Draft populator
  | 'populateDraftData'
  // Validate draft to ready
  | 'validateDraftDataAndPutReadyEvent'
  // Ready-to-Submitted
  | 'launchPieriandxFromReadyEvent'
  // Post-submission event conversion
  | 'monitorPdxRuns';

export const stateMachineNameList: StateMachineName[] = [
  // Glue code
  'glueSucceededEventsToDraftUpdate',
  // Draft populator
  'populateDraftData',
  // Validate draft to ready
  'validateDraftDataAndPutReadyEvent',
  // Ready-to-Submitted
  'launchPieriandxFromReadyEvent',
  // Post-submission event conversion
  'monitorPdxRuns',
];

// Requirements interface for Step Functions
export interface StepFunctionRequirements {
  // Event stuff
  needsEventPutPermission?: boolean;
  // SSM Stuff
  needsSsmParameterStoreAccess?: boolean;
  // Needs event rule permissions
  needsEventRulePermissions?: boolean;
}

export interface StepFunctionInput {
  stateMachineName: StateMachineName;
}

export interface BuildStepFunctionProps extends StepFunctionInput {
  lambdaObjects: LambdaObject[];
  eventBus: IEventBus;
  isNewWorkflowManagerDeployed: boolean;
  ssmParameterPaths: SsmParameterPaths;
}

export interface StepFunctionObject extends StepFunctionInput {
  sfnObject: StateMachine;
}

export type WireUpPermissionsProps = BuildStepFunctionProps & StepFunctionObject;

export type BuildStepFunctionsProps = Omit<BuildStepFunctionProps, 'stateMachineName'>;

export const stepFunctionsRequirementsMap: Record<StateMachineName, StepFunctionRequirements> = {
  // Glue code
  glueSucceededEventsToDraftUpdate: {
    needsEventPutPermission: true,
  },
  // Draft populator
  populateDraftData: {
    needsEventPutPermission: true,
    needsSsmParameterStoreAccess: true,
  },
  // Validate draft to ready
  validateDraftDataAndPutReadyEvent: {
    needsEventPutPermission: true,
  },
  // Ready-to-Submitted
  launchPieriandxFromReadyEvent: {
    needsEventPutPermission: true,
    needsEventRulePermissions: true,
    needsSsmParameterStoreAccess: true,
  },
  // Post-submission event conversion
  monitorPdxRuns: {
    needsEventPutPermission: true,
    needsEventRulePermissions: true,
  },
};

export const stepFunctionToLambdasMap: Record<StateMachineName, LambdaName[]> = {
  glueSucceededEventsToDraftUpdate: [
    // Shared pre-ready lambdas
    'comparePayload',
    'getPayload',
    'getWorkflowRunObject',
    'generateWruEventObjectWithMergedData',
    'findLatestWorkflow',
    'getDataFilesFromTso500WorkflowRun',
  ],
  populateDraftData: [
    // Shared pre-ready lambdas
    'comparePayload',
    'getPayload',
    'getWorkflowRunObject',
    'generateWruEventObjectWithMergedData',
    'findLatestWorkflow',
    'getDataFilesFromTso500WorkflowRun',
    // Draft to ready (generic)
    'getLibraries',
    'getFastqRgidsFromLibraryId',
    'getMetadataTags',
    'getFastqIdListFromRgidList',
    // Draft to ready (pieriandx specific)
    'getRedcapTagsForLibraryId',
    'generateCaseMetadata',
    'getCaseMetadataFromRedcap',
    // Validation
    'validateDraftDataCompleteSchema',
  ],
  validateDraftDataAndPutReadyEvent: [
    // Validation
    'validateDraftDataCompleteSchema',
  ],
  launchPieriandxFromReadyEvent: [
    // Ready to ICAv2 WES lambdas
    'generatePieriandxObjects',
    'generateCase',
    'generateSequencerrun',
    'generateInformaticsjob',
    'uploadPieriandxSampleDataToS3',
    // Re update object
    'getPayload',
    'generateWruEventObjectWithMergedData',
  ],
  monitorPdxRuns: [
    // PierianDx to WRSC Event lambdas
    'listActiveWorkflowRuns',
    'getPayload',
    'getInformaticsjobAndReportStatus',
    'generateOutputDataPayload',
    'generateWruEventObjectWithMergedData',
    'comparePayload',
  ],
};
