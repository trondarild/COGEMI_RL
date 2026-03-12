# tests/test_thresholds.py
# thresholds.py is the legacy MBRL agent utility module.
# Context entries require keys: 'Distribution' ({-1,0,1}->float), 'Outcomes' (list), 'States' (list).

from cogemi.learning.thresholds import grid_search_thresholds


def test_threshold_grid_search():
    # Reward must be a list of sample values (-1, 0, 1), not a pre-computed distribution dict
    dilemma_list = [
        {'Action': 'Interrupt', 'State': 'Meeting',      'Reward': [-1, -1, 0, 1]},
        {'Action': 'Interrupt', 'State': 'Conversation', 'Reward': [-1, 0, 0, 0, 1]},
        {'Action': 'Interrupt', 'State': 'Lecture',      'Reward': [-1, -1, -1, 0, 1]},
        {'Action': 'Greet',     'State': 'Meeting',      'Reward': [0, 1, 1, 1]},
        {'Action': 'Greet',     'State': 'Conversation', 'Reward': [-1, 0, 0, 0, 1]},
        {'Action': 'Greet',     'State': 'Lecture',      'Reward': [-1, 0, 0, 1, 1]},
    ]
    # Context entries must have 'Distribution', 'Outcomes', and 'States' keys
    contexts = {
        'Interrupt': {
            'C1': {'Distribution': {-1: 0.5, 0: 0.3, 1: 0.2}, 'Outcomes': [-1, -1, 0, 1],   'States': [['Meeting', [-1, -1, 0, 1]]]},
            'C2': {'Distribution': {-1: 0.2, 0: 0.6, 1: 0.2}, 'Outcomes': [-1, 0, 0, 0, 1], 'States': [['Conversation', [-1, 0, 0, 0, 1]]]},
            'C3': {'Distribution': {-1: 0.7, 0: 0.2, 1: 0.1}, 'Outcomes': [-1, -1, -1, 0, 1], 'States': [['Lecture', [-1, -1, -1, 0, 1]]]},
        },
        'Greet': {
            'C1': {'Distribution': {-1: 0.1, 0: 0.3, 1: 0.6}, 'Outcomes': [0, 1, 1, 1],     'States': [['Meeting', [0, 1, 1, 1]]]},
            'C2': {'Distribution': {-1: 0.2, 0: 0.5, 1: 0.3}, 'Outcomes': [-1, 0, 0, 0, 1], 'States': [['Conversation', [-1, 0, 0, 0, 1]]]},
            'C3': {'Distribution': {-1: 0.3, 0: 0.4, 1: 0.3}, 'Outcomes': [-1, 0, 0, 1, 1], 'States': [['Lecture', [-1, 0, 0, 1, 1]]]},
        },
    }
    list_of_actions = ['Interrupt', 'Greet']
    adding_thresholds = [0.1, 0.2, 0.3]
    merging_thresholds = [0.05, 0.1, 0.15]

    results = grid_search_thresholds(
        dilemma_list=dilemma_list,
        contexts=contexts,
        list_of_actions=list_of_actions,
        adding_thresholds=adding_thresholds,
        merging_thresholds=merging_thresholds,
    )

    assert len(results) == len(adding_thresholds) * len(merging_thresholds)
    for add_t, merge_t, final_ctx in results:
        assert 0.0 <= add_t <= 1.0
        assert 0.0 <= merge_t <= 1.0
        assert isinstance(final_ctx, dict)
        # each action's context entries must have the required keys
        for action, ctx_dict in final_ctx.items():
            for label, entry in ctx_dict.items():
                assert 'Distribution' in entry
                assert 'Outcomes' in entry
                assert 'States' in entry
