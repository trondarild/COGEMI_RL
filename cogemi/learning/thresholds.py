# from cogemi.learning.context_learner import run_mbrl_agent, update_contexts_with_dilemma, merge_similar_contexts
import numpy as np
#import matplotlib.pyplot as plt
from tabulate import tabulate
from scipy.stats import wasserstein_distance
from scipy.optimize import linear_sum_assignment
from collections import Counter
import random
from tqdm import tqdm  

# import seaborn as sns
# from matplotlib import rcParams
# from matplotlib.colors import Normalize
# import pandas as pd

def DKL(d1, d2):
    if not isinstance(d1, np.ndarray) and not isinstance(d2, np.ndarray):
        d1_array = np.array([d1[-1], d1[0], d1[1]])
        d2_array = np.array([d2[-1], d2[0], d2[1]])
        return np.sum(d1_array * np.log(d1_array / d2_array))

    elif isinstance(d1, np.ndarray) and not isinstance(d2, np.ndarray):
        d2_array = np.array([d2[-1], d2[0], d2[1]])
        return np.sum(d1 * np.log(d1 / d2_array))

    elif isinstance(d2, np.ndarray) and not isinstance(d1, np.ndarray):
        d1_array = np.array([d1[-1], d1[0], d1[1]])
        return np.sum(d1_array * np.log(d1_array / d2))

    else:
        return np.sum(d1 * np.log(d1 / d2))

def swJS(d1,d2, N1, N2):
    d1_array = np.array([d1[-1], d1[0], d1[1]])
    d2_array = np.array([d2[-1], d2[0], d2[1]])
    return .5*DKL(d1_array,(N1*d1_array+N2*d2_array)/(N1+N2))+.5*DKL(d2_array,(N1*d1_array+N2*d2_array)/(N1+N2))

# TODO generalise beyond dilemmas
def input_dilemma(dilemma, contexts, list_of_actions, threshold):
    # dilemma['Reward'] must be a list of sample values (e.g. [-1, -1, 0, 1])
    reward_samples = dilemma['Reward']
    reward_distribution = distribution(reward_samples)

    #Is the action performed in this dilemma already in the list of action ?
    #If yes :
    if dilemma['Action'] in list_of_actions :
        #We will iterate over the contexts already in memory
        context_list = list(contexts[dilemma['Action']].keys())
        DKL_context = []
        for i in range(len(context_list)):
            DKL_context.append(DKL(reward_distribution, contexts[dilemma['Action']]['C'+str(i+1)]['Distribution'] )) #Calculate the DKL between the dilemma distribution and the contexts' ones
        min_dkl, context_min_dkl = np.min(DKL_context), np.argmin(DKL_context) #Get the context for which the DKL is minimum

        if min_dkl > threshold :
            contexts[dilemma['Action']]['C'+str(1+len(contexts[dilemma['Action']]))]={
                'Distribution' : reward_distribution,
                'Outcomes' : list(reward_samples),
                'States' : [[dilemma['State'], reward_samples]],
            }   #If the min DKL > threshold, we create a new context

        else : #Else, the current observation is added to an existing context
            contexts[dilemma['Action']]['C'+str(context_min_dkl+1)]['Outcomes'] += list(reward_samples)
            contexts[dilemma['Action']]['C'+str(context_min_dkl+1)]['States'].append([dilemma['State'], reward_samples])
            contexts[dilemma['Action']]['C'+str(context_min_dkl+1)]['Distribution'] = distribution(contexts[dilemma['Action']]['C'+str(context_min_dkl+1)]['Outcomes'])

    #If the action performed is not in the list of action, we add it to the list and create a new context from it.
    else :
        list_of_actions.append(dilemma['Action'])
        contexts[dilemma['Action']] = {
            'C1':{'Distribution' : reward_distribution,
                'Outcomes' : list(reward_samples),
                'States' : [[dilemma['State'], reward_samples]],
            }
        }
        
def merge(contexts, threshold):
    action_list = list(contexts.keys())
    
    #Iterate over actions
    for action in action_list : 
        #We will calculate the swJS divergence for each pair of context for each action
        swJS_list = [[],[]]
        if len(contexts[action]) > 1 : 
            for i in range(len(contexts[action])):
                for j in range(i+1, len(contexts[action])):
                    swJS_list[0].append([i,j])
                    swJS_list[1].append(swJS(contexts[action]['C'+str(i+1)]['Distribution'], contexts[action]['C'+str(j+1)]['Distribution'], len(contexts[action]['C'+str(i+1)]['Outcomes']), len(contexts[action]['C'+str(j+1)]['Outcomes']) ))
            #Take the min value of the swJS divergence for one action 
            min_swJS, context_min_swJS = np.min(swJS_list[1]), np.argmin(swJS_list[0])
            #Compare it to the threshold 
            if min_swJS < threshold : 
                i = swJS_list[0][context_min_swJS][0]
                j = swJS_list[0][context_min_swJS][1]
                n = len(contexts[action])
                #Merge the two contexts
                contexts[action]['C'+str(i+1)]['Outcomes'] = list(contexts[action]['C'+str(i+1)]['Outcomes']) + list(contexts[action]['C'+str(j+1)]['Outcomes'])
                contexts[action]['C'+str(i+1)]['States'] = list(contexts[action]['C'+str(i+1)]['States']) + list(contexts[action]['C'+str(j+1)]['States'])
                contexts[action]['C'+str(i+1)]['Distribution'] = distribution(contexts[action]['C'+str(i+1)]['Outcomes'])
                #Replace the second one by the n^th context of the MBRL agent 
                contexts[action]['C'+str(j+1)]['Outcomes'] = contexts[action]['C'+str(n)]['Outcomes']
                contexts[action]['C'+str(j+1)]['States'] = contexts[action]['C'+str(n)]['States']
                contexts[action]['C'+str(j+1)]['Distribution'] = contexts[action]['C'+str(n)]['Distribution']
                #Delete the last context. It ensures that the contexts go from 1 to N 
                del contexts[action]['C'+str(n)]
    
    return contexts

def MBRL_agent(dilemma_list, contexts, list_of_actions, adding_threshold, merging_threshold):
    for dilemma in dilemma_list : 
        input_dilemma(dilemma, contexts, list_of_actions, adding_threshold)
        merge(contexts, merging_threshold)          
    return contexts 
    #return print_summary(contexts)
    
def normalize_distribution(distribution):
    """
    Normalize a ternary distribution so that the probabilities sum to 1.

    Args:
        distribution (dict): Dictionary with keys -1, 0, and 1 representing judgments.

    Returns:
        dict: Normalized distribution with values rounded to 4 decimals.
    """
    total = sum(distribution.values()) if distribution else 1
    return {k: round(v / total, 4) for k, v in distribution.items()}

def distribution(samples):
    """
    Compute a ternary probability distribution from a list of sample values.

    Args:
        samples (list or array): List of sample values (e.g., [1, -1, 0, 1, 1, ...]).

    Returns:
        dict: Normalized probability distribution over -1, 0, and 1.
    """
    # Count occurrences of each unique value
    unique, counts = np.unique(samples, return_counts=True)

    # Compute relative frequencies
    total = len(samples)
    distribution = {val: count / total for val, count in zip(unique, counts)}

    # Ensure all three values (-1, 0, 1) are present with a minimum probability
    for val in [-1, 0, 1]:
        if val not in distribution:
            distribution[val] = 1e-5  # Small pseudo-count to avoid missing keys

    # Normalize to ensure total probability sums to 1
    total_prob = sum(distribution.values())
    distribution = {key: value / total_prob for key, value in distribution.items()}

    return distribution

def grid_search_thresholds(dilemma_list, contexts, list_of_actions, adding_thresholds, merging_thresholds):
    '''Perform a grid search over adding and merging thresholds for the MBRL agent.
    dilemma_list: list of dilemmas to input to the agent, where dilemmas are dicts with keys 'Action', 'State', and 'Reward'.
    Contexts: initial contexts for the agent, structured as a dict of actions mapping to dicts of contexts (e.g., {'Action1': {'C1': {...}, 'C2': {...}}, 'Action2': {'C1': {...}}}).
    list_of_actions: initial list of actions known to the agent.
    adding_thresholds: list of thresholds to test for adding new contexts.
    merging_thresholds: list of thresholds to test for merging existing contexts.
    Returns a list of tuples (adding_threshold, merging_threshold, final_contexts) for each combination of thresholds.
    '''
    results = []
    for add_thres in tqdm(adding_thresholds, desc="Adding Thresholds"):
        for merge_thres in tqdm(merging_thresholds, desc="Merging Thresholds", leave=False):
            contexts_copy = {action: {ctx: data.copy() for ctx, data in ctx_dict.items()} for action, ctx_dict in contexts.items()}
            final_contexts = MBRL_agent(dilemma_list, contexts_copy, list_of_actions.copy(), add_thres, merge_thres)
            results.append((add_thres, merge_thres, final_contexts))
    return results