import { PythonUvFunction } from '@orcabus/platform-cdk-constructs/lambda';
import { PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';
import { SsmParameterPaths } from '../ssm/interfaces';
import { ISecret } from 'aws-cdk-lib/aws-secretsmanager';
import { IFunction } from 'aws-cdk-lib/aws-lambda';
import { IBucket } from 'aws-cdk-lib/aws-s3';

export type LambdaName =
  // Shared pre-ready lambdas
  | 'comparePayload'
  | 'getPayload'
  | 'getWorkflowRunObject'
  | 'generateWruEventObjectWithMergedData'
  | 'findLatestWorkflow'
  | 'getDataFilesFromTso500WorkflowRun'
  // Glue upstream
  // Draft to ready (generic)
  | 'getLibraries'
  | 'getFastqRgidsFromLibraryId'
  | 'getMetadataTags'
  | 'getFastqIdListFromRgidList'
  // Draft to ready (pieriandx specific)
  | 'getRedcapTagsForLibraryId'
  | 'generateCaseMetadata'
  | 'getCaseMetadataFromRedcap'
  // Validation
  | 'validateDraftDataCompleteSchema'
  // Ready to PierianDx Submission
  | 'generatePieriandxObjects'
  | 'generateCase'
  | 'generateSequencerrun'
  | 'generateInformaticsjob'
  | 'uploadPieriandxSampleDataToS3'
  // Monitor Runs to WRSC events
  | 'generateOutputDataPayload'
  | 'listActiveWorkflowRuns'
  | 'getInformaticsjobAndReportStatus';

export const lambdaNameList: LambdaName[] = [
  // Shared pre-ready lambdas
  'comparePayload',
  'getPayload',
  'getWorkflowRunObject',
  'generateWruEventObjectWithMergedData',
  'findLatestWorkflow',
  'getDataFilesFromTso500WorkflowRun',
  // Glue upstream
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
  // Ready to PierianDx Submission
  'generatePieriandxObjects',
  'generateCase',
  'generateSequencerrun',
  'generateInformaticsjob',
  'uploadPieriandxSampleDataToS3',
  // Monitor Runs to WRSC events
  'generateOutputDataPayload',
  'listActiveWorkflowRuns',
  'getInformaticsjobAndReportStatus',
];

// Requirements interface for Lambda functions
export interface LambdaRequirements {
  needsOrcabusApiTools?: boolean;
  needsPieriandxLayerAccess?: boolean;
  needsRedcapLambdaPermission?: boolean;
  needsSsmParametersAccess?: boolean;
  needsSchemaRegistryAccess?: boolean;
}

// Lambda requirements mapping
export const lambdaRequirementsMap: Record<LambdaName, LambdaRequirements> = {
  // Shared pre-ready lambdas
  comparePayload: {},
  getPayload: {
    needsOrcabusApiTools: true,
  },
  getWorkflowRunObject: {
    needsOrcabusApiTools: true,
  },
  generateWruEventObjectWithMergedData: {
    needsOrcabusApiTools: true,
  },
  findLatestWorkflow: {
    needsOrcabusApiTools: true,
  },
  getDataFilesFromTso500WorkflowRun: {
    needsOrcabusApiTools: true,
  },
  // Glue upstream
  // Draft to ready (generic)
  getLibraries: {
    needsOrcabusApiTools: true,
  },
  getFastqRgidsFromLibraryId: {
    needsOrcabusApiTools: true,
  },
  getMetadataTags: {
    needsOrcabusApiTools: true,
  },
  getFastqIdListFromRgidList: {
    needsOrcabusApiTools: true,
  },
  // Draft to ready (pieriandx specific)
  getRedcapTagsForLibraryId: {
    needsOrcabusApiTools: true,
    needsSsmParametersAccess: true,
  },
  generateCaseMetadata: {
    needsOrcabusApiTools: true,
    needsPieriandxLayerAccess: true,
  },
  getCaseMetadataFromRedcap: {
    needsRedcapLambdaPermission: true,
  },
  // Validation
  validateDraftDataCompleteSchema: {
    needsSchemaRegistryAccess: true,
    needsSsmParametersAccess: true,
  },
  // Ready to PierianDx Submission
  generatePieriandxObjects: {
    needsPieriandxLayerAccess: true,
    needsOrcabusApiTools: true,
  },
  generateCase: {
    needsPieriandxLayerAccess: true,
    needsOrcabusApiTools: true,
  },
  generateSequencerrun: {
    needsPieriandxLayerAccess: true,
    needsOrcabusApiTools: true,
  },
  generateInformaticsjob: {
    needsPieriandxLayerAccess: true,
    needsOrcabusApiTools: true,
  },
  generateOutputDataPayload: {
    needsPieriandxLayerAccess: true,
    needsOrcabusApiTools: true,
  },
  uploadPieriandxSampleDataToS3: {
    needsOrcabusApiTools: true,
    needsPieriandxLayerAccess: true,
  },
  // Monitor Runs to WRSC events
  listActiveWorkflowRuns: {
    needsOrcabusApiTools: true,
  },
  getInformaticsjobAndReportStatus: {
    needsPieriandxLayerAccess: true,
    needsOrcabusApiTools: true,
  },
};

export interface BuildLambdasInput {
  pieriandxLambdaLayer: PythonLayerVersion;
  ssmParameterNames: SsmParameterPaths;
  authTokenLambdaFunction: IFunction;
  redcapLambdaFunction: IFunction;
  s3CredentialsSecret: ISecret;
  s3LookUpBucket: IBucket;
}

export interface BuildLambdaInput extends BuildLambdasInput {
  lambdaName: LambdaName;
}

export interface LambdaObject {
  lambdaName: LambdaName;
  lambdaFunction: PythonUvFunction;
}
