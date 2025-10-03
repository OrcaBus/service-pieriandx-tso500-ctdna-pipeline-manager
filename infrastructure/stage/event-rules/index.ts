/* Event Bridge Rules */
import {
  BuildReadyRuleProps,
  eventBridgeRuleNameList,
  EventBridgeRuleObject,
  EventBridgeRuleProps,
  EventBridgeRulesProps,
  BuildDraftRuleProps,
  ScheduledEventBridgeRuleProps,
} from './interfaces';
import { EventPattern, Rule } from 'aws-cdk-lib/aws-events';
import * as events from 'aws-cdk-lib/aws-events';
import { Construct } from 'constructs';
import {
  DEFAULT_PAYLOAD_VERSION,
  DRAFT_STATUS,
  DRAGEN_TSO500_CTDNA_WORKFLOW_NAME,
  MONITOR_RUNS_FREQUENCY,
  READY_STATUS,
  STACK_PREFIX,
  SUCCEEDED_STATUS,
  WORKFLOW_MANAGER_EVENT_SOURCE,
  WORKFLOW_NAME,
  WORKFLOW_RUN_STATE_CHANGE_DETAIL_TYPE,
  WORKFLOW_RUN_UPDATE_DETAIL_TYPE,
} from '../constants';

/*
https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-create-pattern-operators.html
*/

function buildMonitorPdxRule(scope: Construct, props: ScheduledEventBridgeRuleProps): Rule {
  return new events.Rule(scope, props.ruleName, {
    ruleName: `${STACK_PREFIX}-${props.ruleName}`,
    schedule: events.Schedule.rate(props.scheduleDuration ?? MONITOR_RUNS_FREQUENCY),
  });
}

function upstreamLegacySucceededEventPattern(): EventPattern {
  return {
    detailType: [WORKFLOW_RUN_STATE_CHANGE_DETAIL_TYPE],
    source: [WORKFLOW_MANAGER_EVENT_SOURCE],
    detail: {
      workflowName: [DRAGEN_TSO500_CTDNA_WORKFLOW_NAME],
      status: [SUCCEEDED_STATUS],
    },
  };
}

function buildWorkflowManagerLegacyDraftEventPattern(): EventPattern {
  return {
    detailType: [WORKFLOW_RUN_STATE_CHANGE_DETAIL_TYPE],
    source: [WORKFLOW_MANAGER_EVENT_SOURCE],
    detail: {
      workflowName: [WORKFLOW_NAME],
      status: [DRAFT_STATUS],
    },
  };
}

function buildWorkflowManagerLegacyReadyEventPattern(): EventPattern {
  return {
    detailType: [WORKFLOW_RUN_STATE_CHANGE_DETAIL_TYPE],
    source: [WORKFLOW_MANAGER_EVENT_SOURCE],
    detail: {
      workflowName: [WORKFLOW_NAME],
      status: [READY_STATUS],
      payload: {
        version: [DEFAULT_PAYLOAD_VERSION],
      },
    },
  };
}

function upstreamSucceededEventPattern(): EventPattern {
  return {
    detailType: [WORKFLOW_RUN_UPDATE_DETAIL_TYPE],
    source: [WORKFLOW_MANAGER_EVENT_SOURCE],
    detail: {
      workflow: {
        name: [DRAGEN_TSO500_CTDNA_WORKFLOW_NAME],
      },
      status: [SUCCEEDED_STATUS],
    },
  };
}

function buildWorkflowManagerDraftEventPattern(): EventPattern {
  return {
    detailType: [WORKFLOW_RUN_STATE_CHANGE_DETAIL_TYPE],
    source: [WORKFLOW_MANAGER_EVENT_SOURCE],
    detail: {
      workflow: {
        name: [WORKFLOW_NAME],
      },
      status: [DRAFT_STATUS],
    },
  };
}

function buildWorkflowManagerReadyEventPattern(): EventPattern {
  return {
    detailType: [WORKFLOW_RUN_STATE_CHANGE_DETAIL_TYPE],
    source: [WORKFLOW_MANAGER_EVENT_SOURCE],
    detail: {
      workflow: {
        name: [WORKFLOW_NAME],
      },
      status: [READY_STATUS],
      payload: {
        version: [DEFAULT_PAYLOAD_VERSION],
      },
    },
  };
}

function buildEventRule(scope: Construct, props: EventBridgeRuleProps): Rule {
  return new events.Rule(scope, props.ruleName, {
    ruleName: `${STACK_PREFIX}-${props.ruleName}`,
    eventPattern: props.eventPattern,
    eventBus: props.eventBus,
  });
}

function buildUpstreamSucceededWorkflowRunStateChangeLegacyEventRule(
  scope: Construct,
  props: BuildDraftRuleProps
): Rule {
  return buildEventRule(scope, {
    ruleName: props.ruleName,
    eventPattern: upstreamLegacySucceededEventPattern(),
    eventBus: props.eventBus,
  });
}

function buildUpstreamSucceededWorkflowRunUpdateEventRule(
  scope: Construct,
  props: BuildDraftRuleProps
): Rule {
  return buildEventRule(scope, {
    ruleName: props.ruleName,
    eventPattern: upstreamSucceededEventPattern(),
    eventBus: props.eventBus,
  });
}

function buildWorkflowRunStateChangeDraftLegacyEventRule(
  scope: Construct,
  props: BuildDraftRuleProps
): Rule {
  return buildEventRule(scope, {
    ruleName: props.ruleName,
    eventPattern: buildWorkflowManagerLegacyDraftEventPattern(),
    eventBus: props.eventBus,
  });
}

function buildWorkflowRunStateChangeReadyLegacyEventRule(
  scope: Construct,
  props: BuildReadyRuleProps
): Rule {
  return buildEventRule(scope, {
    ruleName: props.ruleName,
    eventPattern: buildWorkflowManagerLegacyReadyEventPattern(),
    eventBus: props.eventBus,
  });
}

function buildWorkflowRunUpdateDraftEventRule(scope: Construct, props: BuildDraftRuleProps): Rule {
  return buildEventRule(scope, {
    ruleName: props.ruleName,
    eventPattern: buildWorkflowManagerDraftEventPattern(),
    eventBus: props.eventBus,
  });
}

function buildWorkflowRunUpdateReadyEventRule(scope: Construct, props: BuildReadyRuleProps): Rule {
  return buildEventRule(scope, {
    ruleName: props.ruleName,
    eventPattern: buildWorkflowManagerReadyEventPattern(),
    eventBus: props.eventBus,
  });
}

export function buildAllEventRules(
  scope: Construct,
  props: EventBridgeRulesProps
): EventBridgeRuleObject[] {
  const eventBridgeRuleObjects: EventBridgeRuleObject[] = [];

  // Iterate over the eventBridgeNameList and create the event rules
  for (const ruleName of eventBridgeRuleNameList) {
    switch (ruleName) {
      case 'upstreamSucceededEventLegacy': {
        eventBridgeRuleObjects.push({
          ruleName: ruleName,
          ruleObject: buildUpstreamSucceededWorkflowRunStateChangeLegacyEventRule(scope, {
            ruleName: ruleName,
            eventBus: props.eventBus,
          }),
        });
        break;
      }
      case 'upstreamSucceededEvent': {
        eventBridgeRuleObjects.push({
          ruleName: ruleName,
          ruleObject: buildUpstreamSucceededWorkflowRunUpdateEventRule(scope, {
            ruleName: ruleName,
            eventBus: props.eventBus,
          }),
        });
        break;
      }
      case 'wrscDraftLegacy': {
        eventBridgeRuleObjects.push({
          ruleName: ruleName,
          ruleObject: buildWorkflowRunStateChangeDraftLegacyEventRule(scope, {
            ruleName: ruleName,
            eventBus: props.eventBus,
          }),
        });
        break;
      }
      case 'wrscDraft': {
        eventBridgeRuleObjects.push({
          ruleName: ruleName,
          ruleObject: buildWorkflowRunUpdateDraftEventRule(scope, {
            ruleName: ruleName,
            eventBus: props.eventBus,
          }),
        });
        break;
      }
      case 'wrscReadyLegacy': {
        eventBridgeRuleObjects.push({
          ruleName: ruleName,
          ruleObject: buildWorkflowRunStateChangeReadyLegacyEventRule(scope, {
            ruleName: ruleName,
            eventBus: props.eventBus,
          }),
        });
        break;
      }
      case 'wrscReady': {
        eventBridgeRuleObjects.push({
          ruleName: ruleName,
          ruleObject: buildWorkflowRunUpdateReadyEventRule(scope, {
            ruleName: ruleName,
            eventBus: props.eventBus,
          }),
        });
        break;
      }
      case 'monitorPdxRunsSchedule': {
        eventBridgeRuleObjects.push({
          ruleName: ruleName,
          ruleObject: buildMonitorPdxRule(scope, {
            ruleName: ruleName,
          }),
        });
      }
    }
  }

  // Return the event bridge rule objects
  return eventBridgeRuleObjects;
}
