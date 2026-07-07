import { PythonUvFunction } from '@orcabus/platform-cdk-constructs/lambda';
import { PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';
import { SsmParameterPaths } from '../ssm/interfaces';
import { ISecret } from 'aws-cdk-lib/aws-secretsmanager';
import { IFunction } from 'aws-cdk-lib/aws-lambda';
import { IBucket } from 'aws-cdk-lib/aws-s3';

export type LambdaNameList =
  // Shared pre-ready lambdas
  | 'comparePayload'
  | 'getPayload'
  | 'getWorkflowRunObject'
  | 'generateWruEventObjectWithMergedData'
  | 'getMissingSchemaFields'
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
  | 'postSchemaValidation'
  // Commentary Functions
  | 'addPopulateDraftComment'
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

export const lambdaNameList: LambdaNameList[] = [
  // Shared pre-ready lambdas
  'comparePayload',
  'getPayload',
  'getWorkflowRunObject',
  'generateWruEventObjectWithMergedData',
  'getMissingSchemaFields',
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
  'postSchemaValidation',
  // Commentary Functions
  'addPopulateDraftComment',
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
  needsHigherMemory?: boolean;
  needsSsmParametersAccess?: boolean;
  needsSchemaRegistryAccess?: boolean;
  needsExtendedTimeout?: boolean;
  needsWorkflowInfo?: boolean;
  needsRepoUrl?: boolean;
}

// Lambda requirements mapping
export const lambdaRequirementsMap: Record<LambdaNameList, LambdaRequirements> = {
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
  getMissingSchemaFields: {
    needsSchemaRegistryAccess: true,
    needsSsmParametersAccess: true,
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
    needsExtendedTimeout: true,
  },
  getCaseMetadataFromRedcap: {
    needsRedcapLambdaPermission: true,
    needsHigherMemory: true,
  },
  // Validation
  validateDraftDataCompleteSchema: {
    needsSchemaRegistryAccess: true,
    needsSsmParametersAccess: true,
  },
  postSchemaValidation: {
    needsOrcabusApiTools: true,
    needsWorkflowInfo: true,
  },
  // Commentary Functions
  addPopulateDraftComment: {
    needsOrcabusApiTools: true,
    needsWorkflowInfo: true,
    needsRepoUrl: true,
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
  lambdaName: LambdaNameList;
}

export interface LambdaObject {
  lambdaName: LambdaNameList;
  lambdaFunction: PythonUvFunction;
}
