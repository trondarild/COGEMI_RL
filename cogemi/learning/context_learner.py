# cogemi/learning/context_learner.py
import numpy as np
from typing import Any, Dict, List

from cogemi.metrics.divergences import kl_divergence, weighted_js_divergence, estimate_distribution
from cogemi.observe.scenario import Scenario

# Type alias for a single context entry:
# {"Distribution": {-1: float, 0: float, 1: float}, "Outcomes": list, "States": list}
ContextEntry = Dict[str, Any]
# Type alias for the full contexts dict: {action: {"C1": ContextEntry, ...}}
ContextsDict = Dict[str, Dict[str, ContextEntry]]


class ContextLearner:
    def __init__(self, add_threshold: float, merge_threshold: float, metric: str):
        self.add_threshold = add_threshold
        self.merge_threshold = merge_threshold
        self.metric = metric
        self.contexts_dict: ContextsDict = {}
        self.known_actions: List[str] = []

    def fit(self, scenarios: List[Scenario], sample_collection: List[List[float]]) -> List[str]:
        '''Fit the learner with the given scenarios and survey responses.

        sample_collection: list of lists of numerical responses (e.g. -1, 0, 1),
        where each inner list corresponds to the responses for one scenario.
        The order must match the order of scenarios.

        Returns: list of context labels (e.g. "some_action:C1") assigned to each scenario,
                 in the same order as `scenarios`. These are the labels for generalizer.fit().
        '''
        context_labels: List[str] = []
        for scenario, samples in zip(scenarios, sample_collection):
            # NOTE: scenario.id must be in format "prefix_action_state" (e.g. "s_1_2")
            label = self.add(scenario.id, samples)
            context_labels.append(label)
        return context_labels

    def add(self, scenario_id: str, reward_samples: List[float]) -> str:
        '''scenario_id like A_1_2 where A is prefix, 1 is action and 2 is state.
        Returns the context label assigned (e.g. "some_action:C1").
        '''
        dilemma = {
            'Reward': reward_samples,
            'Action': scenario_id.split("_")[1],
            'State': scenario_id.split("_")[2]
        }
        assigned_label = self.update_contexts_with_dilemma(dilemma, self.contexts_dict, self.known_actions, self.add_threshold)
        self.merge_similar_contexts(self.contexts_dict, self.merge_threshold)
        return assigned_label

    def update_contexts_with_dilemma(
        self,
        dilemma: Dict[str, Any],
        contexts_dict: ContextsDict,
        known_actions: List[str],
        threshold: float
    ) -> str:
        """
        Process a dilemma and update existing contexts or create a new one if necessary.

        Arguments:
        - dilemma: dict with 'Reward' (list of floats), 'Action' (str), and 'State' (str)
        - contexts_dict: dict of existing contexts keyed by action then context label
        - known_actions: list of actions already encountered
        - threshold: KL divergence threshold to decide whether to create a new context

        Returns: the context label assigned, in format "action:Cn" (e.g. "cut_in_line:C1")
        """
        action = dilemma['Action']
        reward_distribution = estimate_distribution(dilemma['Reward'])

        if action in known_actions:
            context_list = list(contexts_dict[action].keys())
            DKL_context = []

            for i in range(len(context_list)):
                DKL_context.append(kl_divergence(reward_distribution, contexts_dict[action]['C'+str(i+1)]['Distribution']))

            min_dkl, context_min_dkl = np.min(DKL_context), np.argmin(DKL_context)

            if min_dkl > threshold:
                new_label = 'C' + str(1 + len(contexts_dict[action]))
                contexts_dict[action][new_label] = {
                    'Distribution': reward_distribution,
                    'Outcomes': dilemma['Reward'],
                    'States': [[dilemma['State'], dilemma['Reward']]],
                }
                assigned = new_label
            else:
                assigned = 'C' + str(context_min_dkl + 1)
                contexts_dict[action][assigned]['Outcomes'] = np.concatenate(
                    (contexts_dict[action][assigned]['Outcomes'], dilemma['Reward']))
                contexts_dict[action][assigned]['States'].append([dilemma['State'], dilemma['Reward']])
                contexts_dict[action][assigned]['Distribution'] = estimate_distribution(
                    contexts_dict[action][assigned]['Outcomes'])

        else:
            known_actions.append(action)
            contexts_dict[action] = {
                'C1': {
                    'Distribution': reward_distribution,
                    'Outcomes': dilemma['Reward'],
                    'States': [[dilemma['State'], dilemma['Reward']]],
                }
            }
            assigned = 'C1'

        return f"{action}:{assigned}"

    def merge_similar_contexts(self, contexts_dict: ContextsDict, threshold: float) -> None:
        """
        Merge similar contexts based on JS divergence.

        Arguments:
        - contexts_dict: dict of contexts keyed by action then context label
        - threshold: JS divergence threshold below which contexts are merged
        """
        action_list = list(contexts_dict.keys())

        for action in action_list:
            swJS_list: List[List] = [[], []]

            if len(contexts_dict[action]) > 1:
                for i in range(len(contexts_dict[action])):
                    for j in range(i+1, len(contexts_dict[action])):
                        swJS_list[0].append([i, j])
                        swJS_list[1].append(
                            weighted_js_divergence(contexts_dict[action]['C'+str(i+1)]['Distribution'],
                                contexts_dict[action]['C'+str(j+1)]['Distribution'],
                                len(contexts_dict[action]['C'+str(i+1)]['Outcomes']),
                                len(contexts_dict[action]['C'+str(j+1)]['Outcomes']))
                        )

                min_swJS, context_min_swJS = np.min(swJS_list[1]), np.argmin(swJS_list[1])

                if min_swJS < threshold:
                    i, j = swJS_list[0][context_min_swJS]
                    n = len(contexts_dict[action])

                    print(contexts_dict[action]['C'+str(j+1)])

                    contexts_dict[action]['C'+str(i+1)]['Outcomes'] += contexts_dict[action]['C'+str(j+1)]['Outcomes']
                    contexts_dict[action]['C'+str(i+1)]['States'] += contexts_dict[action]['C'+str(j+1)]['States']
                    contexts_dict[action]['C'+str(i+1)]['Distribution'] = estimate_distribution(contexts_dict[action]['C'+str(i+1)]['Outcomes'])

                    contexts_dict[action]['C'+str(j+1)] = contexts_dict[action]['C'+str(n)]
                    del contexts_dict[action]['C'+str(n)]

    def contexts(self) -> ContextsDict:
        return self.contexts_dict
