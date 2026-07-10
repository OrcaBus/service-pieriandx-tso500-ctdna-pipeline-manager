import * as eventsTargets from 'aws-cdk-lib/aws-events-targets';
import * as events from 'aws-cdk-lib/aws-events';
import {
  AddSfnAsEventBridgeTargetProps,
  eventBridgeTargetsNameList,
  EventBridgeTargetsProps,
} from './interfaces';

export function buildWrscToSfnTarget(props: AddSfnAsEventBridgeTargetProps) {
  // We take in the event detail from the pieriandx ready event
  // And return the entire detail to the state machine
  props.eventBridgeRuleObj.addTarget(
    new eventsTargets.SfnStateMachine(props.stateMachineObj, {
      input: events.RuleTargetInput.fromEventPath('$.detail'),
    })
  );
}

export function buildIcav2WesEventStateChangeToWrscSfnTarget(
  props: AddSfnAsEventBridgeTargetProps
) {
  // We take in the event detail from the icav2 wes state change event
  props.eventBridgeRuleObj.addTarget(
    new eventsTargets.SfnStateMachine(props.stateMachineObj, {
      input: events.RuleTargetInput.fromEventPath('$.detail'),
    })
  );
}

export function buildAllEventBridgeTargets(props: EventBridgeTargetsProps) {
  for (const eventBridgeTargetsName of eventBridgeTargetsNameList) {
    switch (eventBridgeTargetsName) {
      case 'upstreamSucceededEventToGlueSucceededEvents': {
        buildWrscToSfnTarget(<AddSfnAsEventBridgeTargetProps>{
          eventBridgeRuleObj: props.eventBridgeRuleObjects.find(
            (eventBridgeObject) => eventBridgeObject.ruleName === 'upstreamSucceededEvent'
          )?.ruleObject,
          stateMachineObj: props.stepFunctionObjects.find(
            (sfnObject) => sfnObject.stateMachineName === 'glueSucceededEventsToDraftUpdate'
          )?.sfnObject,
        });
        break;
      }

      case 'draftToPopulateDraftDataSfnTarget': {
        buildWrscToSfnTarget(<AddSfnAsEventBridgeTargetProps>{
          eventBridgeRuleObj: props.eventBridgeRuleObjects.find(
            (eventBridgeObject) => eventBridgeObject.ruleName === 'wrscDraft'
          )?.ruleObject,
          stateMachineObj: props.stepFunctionObjects.find(
            (sfnObject) => sfnObject.stateMachineName === 'populateDraftData'
          )?.sfnObject,
        });
        break;
      }

      case 'draftToValidateDraftSfnTarget': {
        buildWrscToSfnTarget(<AddSfnAsEventBridgeTargetProps>{
          eventBridgeRuleObj: props.eventBridgeRuleObjects.find(
            (eventBridgeObject) => eventBridgeObject.ruleName === 'wrscDraft'
          )?.ruleObject,
          stateMachineObj: props.stepFunctionObjects.find(
            (sfnObject) => sfnObject.stateMachineName === 'validateDraftDataAndPutReadyEvent'
          )?.sfnObject,
        });
        break;
      }

      case 'readyToIcav2WesSubmittedSfnTarget': {
        buildWrscToSfnTarget(<AddSfnAsEventBridgeTargetProps>{
          eventBridgeRuleObj: props.eventBridgeRuleObjects.find(
            (eventBridgeObject) => eventBridgeObject.ruleName === 'wrscReady'
          )?.ruleObject,
          stateMachineObj: props.stepFunctionObjects.find(
            (sfnObject) => sfnObject.stateMachineName === 'launchPieriandxFromReadyEvent'
          )?.sfnObject,
        });
        break;
      }

      case 'monitorPdxRuns': {
        buildIcav2WesEventStateChangeToWrscSfnTarget(<AddSfnAsEventBridgeTargetProps>{
          eventBridgeRuleObj: props.eventBridgeRuleObjects.find(
            (eventBridgeObject) => eventBridgeObject.ruleName === 'monitorPdxRunsSchedule'
          )?.ruleObject,
          stateMachineObj: props.stepFunctionObjects.find(
            (sfnObject) => sfnObject.stateMachineName === 'monitorPdxRuns'
          )?.sfnObject,
        });
        break;
      }
    }
  }
}
