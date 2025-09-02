import xml.etree.ElementTree as ET
import xmltodict
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import altair as alt

from livesplit_parser.livesplit_data import LivesplitData

class RunnerData:
    # up to the user to create the dictionary of runners and usernames!
    def __init__(self, runner_data_dict):
        self.runner_data = runner_data_dict

    def add_runner_data(self, username, data):
        if username not in self.runner_data.keys():
            self.runner_data[username] = data
        else:
            # TODO: Add a custom error message that gets thrown here
            print(f"ERROR: User {username} already exists!")
            print("Not adding user")

    def remove_runner_data(self, username):
        if username in self.runner_data.keys():
            del self.runner_data[username]
        else:
            # TODO: Add a custom error message that gets thrown here
            print(f"ERROR: User {username} does not exist!")

    def update_runner_data(self, username, new_data):
        if username in self.runner_data.keys():
            self.runner_data[username] = new_data
        else:
            # TODO: Add a custom error message that gets thrown here
            print(f"ERROR: User {username} does not exist!")

    def get_runner(self, username):
        return self.runner_data[username]

    def plot_percent_past(self, plot=True):
        runner_usernames = list(self.runner_data.keys())
        df = pd.DataFrame(
            columns=self.runner_data[runner_usernames[0]].split_info_df.index.to_list(),
            index=runner_usernames
        )
        
        # Fill df with percent values
        for runner in runner_usernames:
            curr_df = self.runner_data[runner].attempt_info_df
            for col in df.columns:
                df.loc[runner, col] = (
                    curr_df[(curr_df['RunCompleted'] == False) & (curr_df[col].isna())].shape[0]
                    / self.runner_data[runner].num_attempts
                ) * 100

        # Reshape into long format for Altair
        df_long = df.reset_index().melt(
            id_vars="index", 
            var_name="Split", 
            value_name="Percent"
        ).rename(columns={"index": "Runner"})

        # Ensure categorical ordering of splits
        split_order = list(df.columns)

        print(df_long)

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

        # Return chart if requested
        if plot:
            return chart
          
    # def plot_num_attempts_comp(self, plot=True):
    #     names = list(self.runner_data.keys())
    #     num_attempts = []
    #     num_completed_attempts = []
    #     for k in self.runner_data.keys():
    #         num_attempts.append(self.runner_data[k].num_attempts)
    #         num_completed_attempts.append(self.runner_data[k].num_completed_attempts)

    #     data = pd.DataFrame({
    #     'Runner': names,
    #     'Total Attempts': num_attempts,
    #     'Completed Attempts': num_completed_attempts
    #     })
        
    #     data_melted = data.melt(id_vars="Runner", var_name="Attempt Type", value_name="Count")

    #     # Melt the DataFrame for seaborn with attempt types as x-axis
    #     data_melted = data.melt(id_vars="Runner", var_name="Attempt Type", value_name="Count")

    #     # Plot using seaborn
    #     fig, ax = plt.subplots()
    #     sns.barplot(x="Attempt Type", y="Count", hue="Runner", data=data_melted, ax=ax)

    #     # Set labels and title
    #     ax.set_title('Comparison of Total and Completed Attempts for Each Runner')
    #     ax.set_xlabel('Attempt Type')
    #     ax.set_ylabel('Number of Attempts')
    #     plt.xticks(rotation=45)

    #     # Return the figure if plotting is enabled
    #     if plot:
    #         fig = plt.gcf()
    #         return fig

    def plot_num_attempts_comp(self, plot=True):
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

        if plot:
            return chart