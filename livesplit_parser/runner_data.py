import xml.etree.ElementTree as ET
import xmltodict
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import altair as alt

# class used to compare different split files using dict (username:livesplitdata)
class RunnerData:
    # define split comparison using input dict
    def __init__(self, runner_data_dict):
        self.runner_data = runner_data_dict
        runner_main_name = list(self.runner_data.keys())[0]
        for runner_name, runner_dfs in self.runner_data.items():
            if not self._matching_splits(self.runner_data[runner_main_name].split_info_df, runner_dfs.split_info_df):
                raise ValueError(f"Splits for user {runner_name} do not match the split layout with user {runner_main_name}. Please adjust the split files in LiveSplit to match.")

    # add runner to the dict
    def add_runner_data(self, username, data):
        if not self._matching_splits(list(self.runner_data.values())[0].split_info_df, data.split_info_df):
            print(f"ERROR: User {username} does not match split layout of other splits. Please adjust the split file in LiveSplit to match.")
            return None

        if username not in self.runner_data.keys():
            self.runner_data[username] = data
        else:
            print(f"ERROR: User {username} already exists!")
            print("Not adding user")

    # remove runner from dict
    def remove_runner_data(self, username):
        if username in self.runner_data.keys():
            del self.runner_data[username]
        else:
            print(f"ERROR: User {username} does not exist!")

    # update current runner
    def update_runner_data(self, username, new_data):
        if username in self.runner_data.keys():
            self.runner_data[username] = new_data
        else:
            # TODO: Add a custom error message that gets thrown here
            print(f"ERROR: User {username} does not exist!")
        
    # return data of username
    def get_runner(self, username):
        return self.runner_data[username]

    #percentage of runs that pass a split
    def plot_percent_past(self, cumulative=False):

        runner_usernames = list(self.runner_data.keys())

        # create df of just usernames and splits
        df = pd.DataFrame(
            columns=self.runner_data[runner_usernames[0]].split_info_df.index.to_list(),
            index=runner_usernames
        )
        
        # Fill df with percent values
        for runner in runner_usernames:
            curr_df = self.runner_data[runner].attempt_info_df
            for col in df.columns:
                df.loc[runner, col] = (
                    curr_df[(curr_df[col].notna())].shape[0] 
                    / self.runner_data[runner].num_attempts #returns number of non empty entries over total
                ) * 100

        if cumulative:
            return self._plot_percent_past_cumulative(df)
        else:
            return self._plot_percent_past_by_split(df)

    #plots bar chart of completed and attempted runs by player
    def plot_num_attempts_comp(self):
        names = list(self.runner_data.keys())
        num_attempts = []
        num_completed_attempts = []

        for k in self.runner_data.keys():
            num_attempts.append(self.runner_data[k].num_attempts)
            num_completed_attempts.append(self.runner_data[k].num_completed_attempts)

        data = pd.DataFrame({
            'Runner': names,
            'Total': num_attempts,
            'Completed': num_completed_attempts
        })

        # Melt the DataFrame for long-form plotting
        data_melted = data.melt(id_vars="Runner", var_name="Attempt Type", value_name="Count")

        # Altair grouped bar chart
        chart = alt.Chart(data_melted).mark_bar().encode(
            x=alt.X('Attempt Type:N', title='Attempt Type', axis=alt.Axis(labelAngle=45)),
            y=alt.Y('Count:Q', title='Number of Attempts'),
            color='Runner:N',
            xOffset='Runner:N'  # this groups bars by runner within each attempt type
        ).properties(
            title='Comparison of Total and Completed Attempts for Each Runner'
        )

        return chart


    ###### HELPER FUNCTIONS ######
    #returns true/false of whether two dataframes have the same number of splits
    def _matching_splits(self, main_df, new_df):
        return len(main_df.index) == len(new_df.index)

    #plots bar chart of completion percentage of each split for each runner (cumulative)
    def _plot_percent_past_cumulative(self, df):        

        # Reshape into long format for Altair
        df_long = df.reset_index().melt(
            id_vars="index", 
            var_name="Split", 
            value_name="Percent"
        ).rename(columns={"index": "Runner"})

        # Ensure categorical ordering of splits
        split_order = list(df.columns)

        # Create Altair grouped bar chart (all bars on the same plot)
        chart = (
            alt.Chart(df_long)
            .mark_bar()
            .encode(
                x=alt.X("Split:N", title="Split", sort=split_order, axis=alt.Axis(labelAngle=45)),
                y=alt.Y("Percent:Q", title="Percent"),
                color=alt.Color("Runner:N", title="Runner"),
                xOffset="Runner:N"  # This ensures bars for different runners are side-by-side per split
            )
            .properties(
                title="Percentage of Runs Past A Given Split",
                width=500,
                height=300
            )
        )

        return chart
    
    #plot of completion percentage of each split for each runner (by individual split)
    def _plot_percent_past_by_split(self, df):

        for row in range(len(df)):
            for col in range(df.shape[1] - 1, 0, -1) : #don't change first row
                df.iloc[row, col] = (df.iloc[row,col] / df.iloc[row, col-1]) * 100 #divide each row by previous

        # Reshape into long format for Altair
        df_long = df.reset_index().melt(
            id_vars="index", 
            var_name="Split", 
            value_name="Percent"
        ).rename(columns={"index": "Runner"})

        # Ensure categorical ordering of splits
        split_order = list(df.columns)

        # Create Altair grouped bar chart (all bars on the same plot)
        chart = (
            alt.Chart(df_long)
            .mark_bar()
            .encode(
                x=alt.X("Split:N", title="Split", sort=split_order, axis=alt.Axis(labelAngle=45)),
                y=alt.Y("Percent:Q", title="Percent"),
                color=alt.Color("Runner:N", title="Runner"),
                xOffset="Runner:N"  # This ensures bars for different runners are side-by-side per split
            )
            .properties(
                title="Tendency to Pass Each Individual Split",
                width=500,
                height=300
            )
        )

        return chart
