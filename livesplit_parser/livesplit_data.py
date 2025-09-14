from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import altair as alt

from typing import Any

def _clean_text(text: str | None) -> str | None:
    """Strip whitespace and return None if text is empty or None."""
    if text is None:
        return None
    cleaned = text.strip()
    return cleaned if cleaned else None

class LivesplitData:
    game_name: str | None
    category_name: str | None
    time_key: str
    platform: str | None
    region: str | None
    num_attempts: int
    num_completed_attempts: int
    percent_runs_completed: float
    metadata: dict[str:Any] | None
    attempt_info_df: pd.DataFrame
    split_info_df: pd.DataFrame

    def __init__(self, 
                 game_name: str | None,
                 category_name: str | None,
                 platform: str | None,
                 region: str | None,
                 num_attempts: int,
                 num_completed_attempts: int,
                 percent_runs_completed: float,
                 metadata: dict,
                 attempt_info_df: pd.DataFrame,
                 split_info_df: pd.DataFrame,
                 time_key: str = 'RealTime') -> None:
        # Ensure time_key is valid
        if time_key not in ("RealTime", "GameTime"):
            raise ValueError("time_key must be either 'RealTime' or 'GameTime'")
        
        self.game_name = game_name
        self.category_name = category_name
        self.time_key = time_key
        self.platform = platform
        self.region = region
        self.num_attempts = num_attempts
        self.num_completed_attempts = num_completed_attempts
        self.percent_runs_completed = percent_runs_completed
        self.metadata = metadata
        self.attempt_info_df = attempt_info_df
        self.split_info_df = split_info_df

    def __repr__(self) -> str:
        return (f"LivesplitData(game='{self.game_name}', category='{self.category_name}', "
                f"attempts={len(self.attempt_info_df)}, segments={len(self.split_info_df)})")

    @classmethod
    def read_lss(cls, file_path: str | Path, time_key: str = 'RealTime') -> LivesplitData:
        # Ensure time_key is valid
        if time_key not in ("RealTime", "GameTime"):
            raise ValueError("time_key must be either 'RealTime' or 'GameTime'")
        
        tree = ET.parse(file_path)
        root = tree.getroot()

        # ---- Basic metadata ----
        game_name = _clean_text(root.findtext("GameName"))
        category_name = _clean_text(root.findtext("CategoryName"))
        platform = _clean_text(root.findtext("Metadata/Platform"))
        region = _clean_text(root.findtext("Metadata/Region"))

        # Collect all child text/attributes under <Metadata>
        metadata = {}
        metadata_elem = root.find("Metadata")
        if metadata_elem is not None:
            for child in metadata_elem:
                if child.text and child.text.strip():
                    metadata[child.tag] = child.text.strip()
                elif child.attrib:
                    metadata[child.tag] = dict(child.attrib)

        # ---- Parse attempts ----
        attempts_data = []
        for attempt in root.findall("./AttemptHistory/Attempt"):
            attempt_data = {k: v for k, v in attempt.attrib.items()}
            for child in attempt:
                if child.tag == time_key:
                    attempt_data[child.tag] = _clean_text(child.text)
            attempts_data.append(attempt_data)

        attempts_df = pd.DataFrame(attempts_data)
        if not attempts_df.empty and "id" in attempts_df.columns:
            attempts_df["id"] = attempts_df["id"].astype(str)

        # ---- Data cleaning ----
        attempts_df[['started', 'ended']] = attempts_df[['started', 'ended']].apply(pd.to_datetime)
        attempts_df[['isStartedSynced', 'isEndedSynced']] = attempts_df[['isStartedSynced', 'isEndedSynced']].astype(bool)
        attempt_count = len(attempts_df)
        completed_attempt_count = attempts_df['RealTime'].count()
        percent_complete = completed_attempt_count / attempt_count * 100
        attempts_df['RunCompleted'] = attempts_df['RealTime'].notna()
        attempts_df['RealTime'] = attempts_df['RealTime'].fillna(attempts_df['ended'] - attempts_df['started'])
        attempts_df['RealTime'] = attempts_df['RealTime'].apply(pd.to_timedelta)

        # ---- Parse segments ----
        segments_data = []
        for seg in root.findall("./Segments/Segment"):
            seg_name = _clean_text(seg.findtext("Name"))
            best_split_time = _clean_text(seg.findtext("BestSegmentTime/RealTime"))
            pb_split_time = _clean_text(seg.findtext("SplitTimes/SplitTime[@name='Personal Best']/RealTime"))

            segments_data.append({
                "Name": seg_name,
                "BestSegment": best_split_time,
                "PersonalBestSplitTime": pb_split_time
            })
        segments_df = pd.DataFrame(segments_data)
        segments_df[['BestSegment', 'PersonalBestSplitTime']] = segments_df[['BestSegment', 'PersonalBestSplitTime']].apply(pd.to_timedelta)

        # ---- Add SegmentHistory to attempts ----
        for seg in root.findall("./Segments/Segment"):
            seg_name = _clean_text(seg.findtext("Name"))
            if not seg_name:
                continue
            seg_times = {}
            for time_entry in seg.findall("./SegmentHistory/Time"):
                att_id = time_entry.attrib.get("id")
                rt = _clean_text(time_entry.findtext("RealTime"))
                if att_id is not None:
                    seg_times[att_id] = rt
            if not attempts_df.empty:
                attempts_df[seg_name] = attempts_df["id"].map(seg_times)

        # ---- Set the index to the name of the splits ----
        attempts_df.set_index('id', inplace=True)
        segments_df.set_index('Name', inplace=True)

        attempts_df[segments_df.index.to_list()] = attempts_df[segments_df.index.to_list()].apply(pd.to_timedelta)
        attempts_df.index = attempts_df.index.astype(int)

        # ---- Add additional information to segments_df ----
        segments_df['PersonalBest'] = segments_df['PersonalBestSplitTime'].diff().fillna(segments_df['PersonalBestSplitTime'])
        segments_df['BestSegmentSplitTime'] = segments_df['BestSegment'].cumsum()
        segments_df = segments_df.reindex(columns=['PersonalBest', 'PersonalBestSplitTime', 'BestSegment', 'BestSegmentSplitTime'])
        segments_df = cls.__compute_splits_stats(attempts_df, segments_df)
        segments_df = cls.__compute_runs_passed(attempts_df, segments_df)

        attempts_df = cls.__add_float_seconds_cols(attempts_df, ['RealTime'] + attempts_df.columns.to_list()[6:])
        segments_df = cls.__add_float_seconds_cols(segments_df, ['PersonalBest', 'BestSegment', 'StDev', 'Average', 'Median'])

        return cls(
            game_name=game_name,
            category_name=category_name,
            platform=platform,
            region=region,
            num_attempts=attempt_count,
            num_completed_attempts=completed_attempt_count,
            percent_runs_completed=percent_complete,
            metadata=metadata,
            attempt_info_df=attempts_df,
            split_info_df=segments_df,
        )

    def export_data(self) -> None:
        # Specify the Excel file path
        excel_file_path = f'{self.name}.xlsx'
        df1 = self.attempt_info_df[[v for v in self.attempt_info_df.columns if not '_Sec' in v]]
        df2 = self.split_info_df[['PersonalBest', 'PersonalBestSplitTime', 'BestSegment', 'BestSegmentSplitTime', 'StDev', 'Average', 'AverageSplitTime', 'Median', 'MedianSplitTime', 'NumRunsPassed', 'PercentRunsPassed']]

        # Create a Pandas Excel writer using ExcelWriter
        with pd.ExcelWriter(excel_file_path, engine='xlsxwriter') as writer:
            # Write each dataframe to a different sheet
            df1.to_excel(writer, sheet_name='Attempt Info')
            df2.to_excel(writer, sheet_name='Splits Info')

    def plot_num_resets(self) -> alt.Chart:
        df = self.attempt_info_df[['RunCompleted']]
        num_resets_dict = {}
        count = 0

        for i in df.index:
            if df.at[i, 'RunCompleted']:
                num_resets_dict[i] = count
                count = 0
            else:
                count += 1

        # Convert dictionary to DataFrame
        plot_df = pd.DataFrame(list(num_resets_dict.items()), columns=["Attempt", "NumResets"])

        # Create Altair line plot
        chart = alt.Chart(plot_df).mark_line(point=True).encode(
            x="Attempt",
            y="NumResets",
            tooltip=["Attempt", "NumResets"]
        ).properties(
            title="Times Reset Between Completed Runs",
            width=800,
            height=400
        )

        return chart

    def chance_run_continues(self, split_name: str) -> float:
        df = self.split_info_df[['NumRunsPassed']]
        
        #set curr to the # of attempts making it past the previous split
        curr = self.num_attempts
        for i in df.index:
            if i == split_name:
                previous = curr
            curr = df['NumRunsPassed'][i]
        # %of runs (which made it to this split) that made it past this split
        return df['NumRunsPassed'][split_name] / previous * 100
    
    def percent_runs_past(self, split_name) -> float:
        # %of runs that made it past this split
        return self.split_info_df['NumRunsPassed'][split_name] / self.num_attempts * 100
    
    def plot_completed_over_time(self, only_pbs=False, drop_na=False, time_limit=None, plot=True) :
        #set ids from 0, remove useless columns
        df = self.__get_completed_runs_data()[['ended', self.time_key]].reset_index(drop=True)
        
        #max time info and drops run with skipped splits
        time =9999999
        if time_limit != None:
            time = self.__convert_timestr_to_float(time_limit)/60
        if drop_na:
            df.dropna(inplace=True)

        lis = []
        lis2 = []

        #determine first finished run (for only pbs)
        lowest = self.__convert_timestr_to_float(df[self.time_key][0])
        
        #create arrays of times to graph
        if only_pbs: #add only pbs
            for i in range(self.num_completed_attempts):
                #check if current run was a pb or not, add to graph if so
                curr = self.__convert_timestr_to_float(df[self.time_key][i])/60
                if curr < lowest and curr < time:
                    lis.append(curr)
                    lis2.append(df['ended'][i])
                    lowest = curr
                
        else : #add all completed runs
            for i in range(self.num_completed_attempts):
                curr = self.__convert_timestr_to_float(df[self.time_key][i])/60
                if curr < time :
                    lis.append(self.__convert_timestr_to_float(df[self.time_key][i]) / 60)
                    lis2.append(df['ended'][i])
        
        #plot info
        sns.lineplot(y= lis, x= lis2, marker='o', linestyle='-')
        
        plt.title('Completed Runs Over Time')
        plt.xlabel('Date')
        plt.ylabel('Run Times (m)')
        plt.xticks(rotation=90)
        if plot:
            fig = plt.gcf()
            return fig


    def plot_splits_violin_plot(self, completed_runs=False, drop_na=True, plot=True):
        data = self.attempt_info_df[[c for c in self.attempt_info_df.columns if '_Sec' in c and c not in ['RealTime_Sec', 'GameTime_Sec']]]
        if completed_runs:
            data = self.__get_completed_runs_data()[[c for c in data.columns if '_Sec' in c and c not in ['RealTime_Sec', 'GameTime_Sec']]]
        data.rename(columns={c:c[:-4] for c in data.columns}, inplace=True)
        if drop_na:
            data.dropna(inplace=True)
        data = pd.melt(data, var_name='Split Name', value_name='Split Length (Sec)')
        sns.violinplot(x='Split Name', y='Split Length (Sec)', data=data)
        plt.xticks(rotation=90)
        plt.title('Split Time Distributions')
        if plot:
            fig = plt.gcf()
            return fig

    def plot_completed_runs_lineplot(self, drop_na=True, scale='seconds', plot=True):
        data = self.__get_completed_runs_data()
        plot_cols = [c for c in data.columns if '_Sec' in c and c not in ['RealTime_Sec', 'GameTime_Sec']]
        data = data[plot_cols]
        data.rename(columns = {c:c[:-4] for c in data.columns}, inplace=True)

        if drop_na:
            data.dropna(inplace=True)

        for c in data.columns:
            if drop_na:
                avg = data[c].mean()
            else:
                avg = self.__convert_timestr_to_float(self.split_info_df['Average'][c])
            if scale == 'minutes':
                avg /= 60

            for i in data.index:
                if not pd.isna(data[c][i]):
                    if scale == 'seconds':
                        data.loc[i, c] = data[c][i] - avg
                    elif scale == 'minutes':
                        data.loc[i, c] = (data[c][i]/60) - avg

        fig, ax = plt.subplots()
        for index, row in data.iterrows():
            if int(index) != self.__get_pb_id():
                ax.plot(row.index, row.values, color='grey')
            
        if self.__get_pb_id() in data.index:
            ax.plot(row.index, row.values, color='red', label='Personal Best')
        plt.xlabel('Split Name')
        plt.xticks(rotation=90)
        plt.ylabel('Deviation From Mean (Seconds)')
        plt.title('Run Time Distributions')
        plt.legend()
        if plot:
            fig = plt.gcf()
            return fig

    def plot_completed_runs_heatmap(self, drop_na=True, plot=True):
        data = self.__get_completed_runs_data()
        plot_cols = [c for c in data.columns if '_Sec' in c and c not in ['RealTime_Sec', 'GameTime_Sec']]
        data = data[plot_cols]
        data.rename(columns={c:c[:-4] for c in data.columns}, inplace=True)
        
        if drop_na:
            data.dropna(inplace=True)

        for c in data.columns:
            if drop_na:
                avg = data[c].mean()
            else:
                avg = self.__convert_timestr_to_float(self.split_info_df['Average'][c])

            for i in data.index:
                if not pd.isna(data[c][i]):        
                    data.loc[i, c] = data[c][i] - avg

        hm = sns.heatmap(data=data, linewidths=0.5, linecolor='black')

        plt.title('Heatmap of Completed Run Splits (Compared to Avg)')
        plt.xlabel('Split Name')
        plt.xticks(rotation=90)
        plt.ylabel('Completed Run ID')
        if plot:
            fig = plt.gcf()
            return fig
        
    ##################### CLASS HELPER FUNCTIONS ##############
    def __compute_splits_stats(attempts_df: pd.DataFrame, segments_df: pd.DataFrame) -> pd.DataFrame:
        split_names = segments_df.index.to_list()
        average_splits = {split:None for split in split_names}
        median_splits = {split:None for split in split_names}
        std_splits = {split:None for split in split_names}

        for split in split_names:
            average_splits[split] = attempts_df[split].mean(skipna=True)
            median_splits[split] = attempts_df[split].median(skipna=True)
            std_splits[split] = attempts_df[split].std(skipna=True)

        segments_df['StDev'] = segments_df.index.map(std_splits)
        segments_df['Average'] = segments_df.index.map(average_splits)
        segments_df['AverageSplitTime'] = segments_df['Average'].cumsum()
        segments_df['Median'] = segments_df.index.map(median_splits)
        segments_df['MedianSplitTime'] = segments_df['Median'].cumsum()

        return segments_df

    
    def __compute_runs_passed(attempts_df: pd.DataFrame, segments_df: pd.DataFrame) -> pd.DataFrame:
        split_names = segments_df.index.to_list()
        num_runs_passed = {split:None for split in split_names}
        percent_runs_passed = {split:None for split in split_names}
        total_runs = len(attempts_df.index)

        for split in split_names:
            num_runs = attempts_df[split].count()
            num_runs_passed[split] = num_runs
            percent_runs_passed[split] = num_runs / total_runs * 100

        segments_df['NumRunsPassed'] = segments_df.index.map(num_runs_passed)
        segments_df['PercentRunsPassed'] = segments_df.index.map(percent_runs_passed)

        return segments_df

    @classmethod
    def __convert_timestr_to_float(cls, time_str: pd.Timedelta) -> float:
        if time_str == 'nan':
            return float('nan')

        return time_str.total_seconds()

    @classmethod
    def __add_float_seconds_cols(cls, df: pd.DataFrame, col_names: list[str]) -> pd.DataFrame:
        for c in col_names:
            vals = []

            for i in df.index:
                if pd.isna(df[c][i]):
                    vals.append(np.nan)
                else:
                    vals.append(cls.__convert_timestr_to_float(df[c][i]))

            df[c+'_Sec'] = vals
            df[c+'_Sec'] = df[c+'_Sec'].astype(float)

        return df
    
    def __get_completed_runs_data(self) -> pd.DataFrame:
        return self.attempt_info_df[self.attempt_info_df['RunCompleted']]

    def __get_pb_id(self) -> int:
        return int(self.__get_completed_runs_data()[self.time_key].idxmin())


