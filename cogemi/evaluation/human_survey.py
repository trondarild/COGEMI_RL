# cogemi/evaluation/human_survey.py
import pandas as pd
import numpy as np
from natsort import natsorted
from collections import Counter
import random
from typing import Dict, List


class HumanSurveyEvaluator:
    def __init__(self, judgment_map: Dict[str, float], valid_responses: int = 30):
        """judgment_map: mapping from human judgment labels to numerical values for reward distribution
        e.g. {"Inappropriate": -1, "Neutral": 0, "Appropriate": 1}
        """
        self.judgment_map = judgment_map
        self.valid_responses = valid_responses

    def aggregate(self, responses: pd.DataFrame) -> List[Dict]:
        """
        responses: pd.DataFrame read from CSV
        returns: List of dicts with keys 'Action', 'Reward', and 'State'
                 where 'Reward' is a list of numerical values corresponding to human judgments
        """
        # NB: copied from cometh notebook
        df = responses
        # Define new, meaningful column names for the dataset
        new_column_names = ['Timestamp', 'participant_ID', 'Consent', 'question_ID', 'Moral Judgment', 'Age', 'Gender', 'Nationality', 'Group']

        # Assign these new column names to the DataFrame
        df.columns = new_column_names

        # Step 1: Identify participants who answered exactly <valid_responses> questions (complete responders)
        counts = df['participant_ID'].value_counts()
        valid_participants = counts[counts == self.valid_responses].index

        # Step 2: Filter the DataFrame to keep only data from these valid participants
        df2 = df[df['participant_ID'].isin(valid_participants)]

        # Step 3: Print the number of participants with exactly 30 responses
        print(f"Number of participants with exactly 30 responses: {len(valid_participants)}")

        # Remove duplicate rows to keep only one record per participant (for demographic data)
        df_unique = df2.drop_duplicates(subset='participant_ID')

        # Count the number of participants per nationality
        nationality_counts = df_unique['Nationality'].value_counts()

        # Calculate the mean and standard deviation of participants' ages
        mean_age = df_unique['Age'].mean()
        std_age = df_unique['Age'].std()

        # Print nationality counts and age statistics
        print("Number of participants per nationality:")
        print(nationality_counts)
        print(f"\nMean age: {mean_age:.2f}")
        print(f"Age standard deviation: {std_age:.2f}")

        # Calculate the proportion of each gender within the filtered participants (divided by 30 questions per participant)
        gender_counts = df2['Gender'].value_counts() / 30
        print("\nProportion of responses by gender:")
        print(gender_counts)

        # Initialize an empty list to store processed data dictionaries
        modified_result_list: List[Dict] = []

        # Group the filtered DataFrame by question_ID and process each group
        for _id, group in df2.groupby('question_ID'):
            # Extract the action code from question_ID, format assumed to be "s_1_3"
            # where "1" is the action code. Adjust as needed based on actual format.
            action = _id.split('_')[1]

            # Map 'Moral Judgment' text to numerical values using the defined mapping
            reward = group['Moral Judgment'].map(self.judgment_map).tolist()

            # The state corresponds to the third segment in the question_ID format "s_1_3"
            states = _id.split('_')[2]

            # Create a dictionary for each question with action, reward list, and state
            result_dict = {'Action': action, 'Reward': reward, 'State': states}

            # Append this dictionary to the list
            modified_result_list.append(result_dict)
        return modified_result_list
