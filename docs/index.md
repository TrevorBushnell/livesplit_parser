# `livesplit-parser`: A Python Package to Parse Your Livesplit Data

`livesplit-parser` is a package that lets you parse the information from within your Livesplit files. Your Livesplit files are just an XML file, which means it is easy to programmatically pull your data into a table. While many packages like this already exist, we've taken it a step further and included other functions for visualizing your data. We also have a feature that lets you export your data to an Excel sheet so that you can visualize and edit your information in a medium that is more comfortable for you. Inspiration from this project was greatly influenced by [Chipmedal's MK8D livesplit parser](https://github.com/Chipdelmal/mk8dLivesplit).

You can view the full changelog and updates with each release of the package on our [GitHub releases page](https://github.com/TrevorBushnell/livesplit_parser/releases). Additionally, please leave any bugs or future updates you would like added on our [Issues page](https://github.com/TrevorBushnell/livesplit_parser/issues) on GitHub. 

## Install Instructions

Simply install the package in your desired python environment by running:

```
pip install livesplit_parser
```

## `LivesplitData`

The `LivesplitData` class contains all the data within your Livesplit file. There's two `pandas.DataFrame` objects that contain the data within your Livesplit file, as well as some other private variables containing information about your attempts. 

To instantiate the package, simply pass the filepath to your Livesplit file into the constructor:

```python
from livesplit_parser import LivesplitData

your_run = LivesplitData('path/to/your/Livesplit/file')
```

Optionally, you can specify whether you want to pull `RealTime` or `GameTime` out of your splits by passing in the parameter `time_key` into the constructor. The default value for `time_key` is `time_key=RealTime`. As such, if you want to load in `GameTime` for your splits, your code would look like the following:

```python
from livesplit_parser import LivesplitData

your_run = LivesplitData('path/to/your/Livesplit/file', time_key='GameTime')
```

Passing in anything other than `RealTime` or `GameTime` into `time_key` will result in a `ValueError`.

These are the following private member variables you have access to with every `LivesplitData` object:

* `LivesplitData.game_name -> str`: the game the splits are based on
* `LivesplitData.category_name -> str`: the category the splits are based on
* `LivesplitData.time_key -> str`: Whether data is being read with `RealTime` or `GameTime`. Must be one of those two values, otherwise raises a `ValueError`
* `LivesplitData.platform -> str | None`: The platform the speedruns were done on. May not exist.
* `LivesplitData.region -> str | None`: The region the version of the game is run. May not exist.
* `LivesplitData.num_attempts -> int`: the number of attempts for your run
* `LivesplitData.num_completed_attempts -> int`: the number of attempts that were also completed runs
* `LivesplitData.percent_runs_completed -> float`: the percentage of all your attempts that were completed (this is just `LivesplitData.num_completed_attempts / LivesplitData.num_attempts * 100`)
* `LivesplitData.metadata -> dict | None`: Additional metadata stored in the splits. This is a dictionary of string keys to additional strings, dicts, floats, etc. Parts or all of the metadata may not exist.
* `LivesplitData.attempt_info_df -> pandas.DataFrame`: A `pandas.DataFrame` object containing information about every attempt. Each row is an attempt indexed by an ID. The columns of the dataframe are as follows:
  * `started`: timestamp of when the attempt started
  * `isStartedSynced`: ?????
  * `ended`: timestamp of when the attempt ended
  * `isEndedSynced`: ?????
  * `RunCompleted`: If `True`, the attempt was a completed run. If `False`, the attempt was not a completed run
  * `RealTime`: If not a completed run, shows the time the attempt lasted for. If a completed run, shows the final time of the run.
  * Every column afterwards is the name of a split and the length of that segment for that attempt
* `LiveSplitData.split_info_df -> pandas.DataFrame`: A `pandas.DataFrame` object containing general information about every segment in your run. Each row is an individual split in your run. The columns of the dataframe are as follows:
  * `PersonalBest`: the **segment time** for your Personal Best
  * `PersonalBestSplitTime`: the **split time** for your Personal Best
  * `BestSegment`: the fastest time you have completed that split
  * `BestSegmentSplitTime`: the **split times** for your best segments if your best segments were a completed run
  * `Average`: the average length of a given split
  * `AverageSegmentSplitTime`: the **split times** for your average segments if your average segments were a completed run
  * `Median`: the median length of a given split
  * `MedianSegmentSplitTime`: the **split times** for your median segments if your median segments were a completed run
  * `NumRunsPassed`: The number of attempts that completed that split
  * `PercentRunsPassed`: The percentage of attempts that completed that split
* `LivesplitData.game_name`: The name of the game being speedran according to the splits
* `LivesplitData.game_icon`: The game icon saved to the splits
* `LivesplitData.category_name`: the name of the category being run
* `LivesplitData.layout_path`: the layout path used for the splits
* `LivesplitData.platform_name`: the name of the platform the speedruns were attempted on
* `LivesplitData.platform_uses_emulator`: is `True` if the runs were done using an emulator, is `False` otherwise
* `LivesplitData.offset`: the offset used by the splits
* `LivesplitData.version`: the game version being run on

From here, you can use the other included functions (listed below) to get some plots about the data within your Livesplit file.

### `LivesplitData.export_data()`

Writes the data within the Livesplit file to an Excel sheet. The first sheet is the data for each specific attempt, and the second sheet is the info for each of your splits. The name of the sheet will be the name of the split file by default.

### `LivesplitData.plot_num_resets() -> altair.Chart`

Takes the attempt data and plots the number of resets on the y-axis between each completed run whose ID is on the x-axis. This aims to show how reset-prone you were during different times, with lower points indicating less resets. Returns an altair Chart that can be used for data analysis.

### `LivesplitData.chance_run_continues(split_name -> str) -> float`

Assuming your run makes it to `split_name`, returns the percentage of runs that get past `split_name`.

* `split_name`: Determines which split to analyze. Must match the split name exactly, *including subsplit notation*.

### `LivesplitData.percent_runs_past(split_name -> str)`

Returns the percentage of runs that get past `split_name` (this information is just pulled from `LivesplitData.split_info_df['PercentRunsPassed']`)

* `split_name`: Determines which split to analyze. Must match the split name exactly, *including subsplit notation*.

### `LivesplitData.plot_completed_over_time(only_pbs -> bool, drop_na -> bool, time_limit -> str, plot -> bool)`

Graphs completed runs by the date performed. Y-axis shows the length of the run, and X-axis shows the date completed. 

* `only_pbs`: Indicates whether to show all completed runs if set to `False`, or only runs that were personal bests at the time if set to `True`. The default value is set to `False`.
* `drop_na`: Whether to include rows that have missing data from your plot. The default value is set to `False`.
* `time_limit`: Determines an optional upper bound for times included in the plot. Must be in the format 'hh:mm:ss'. No upper bound by default.
* `plot`: Determines whether you want to see this as a standalone graph. Setting this to `True` will cause `plt.show()` to be run. Setting this to `False` will cause `plt.show()` to not be running, allowing you to add more graphs to your plot should you want to do that. The default value is set to `True`.

### `LivesplitData.plot_splits_violin_plot(completed_runs -> bool, drop_na -> bool, plot -> bool)`

Creates a violin plot using the segments in your splits data. To read a violin plot, the length from top to bottom is the range of your data, and the thickness is the number of data points that are close to that specific y-value. Therefore, a thicker part of the range means more of your values are clustered in that area whereas a thinner part means less values are clustered in that area.

* `completed_runs`: Whether to only include completed runs in the data to plot. The default value is set to `True`.
* `drop_na`: Whether to include rows that have missing data from your plot. The default value is set to `True`.
* `plot`: Determines whether you want to see this as a standalone graph. Setting this to `True` will cause `plt.show()` to be run. Setting this to `False` will cause `plt.show()` to not be running, allowing you to add more graphs to your plot should you want to do that. The default value is set to `True`.


### `LivesplitData.plot_completed_runs_lineplot(drop_na -> bool, scale -> str, plot -> bool)`

Creates a lineplot of all your completed runs. Your splits names are on the x-axis, and the difference in the time of that segment from the mean is on the y-axis. This lets you easily visualize which segments you need more practice on.

* `drop_na`: Whether to include rows that have missing data from your plot. The default value is set to `True`.
* `scale`: Whether the scale of the y-axis should be in seconds or minutes. The default is `seconds`. Passing anything other than `seconds` or `minutes` will result in an error. 
* `plot`: Determines whether you want to see this as a standalone graph. Setting this to `True` will cause `plt.show()` to be run. Setting this to `False` will cause `plt.show()` to not be running, allowing you to add more graphs to your plot should you want to do that. The default value is set to `True`.


### `LivesplitData.plot_completed_runs_heatmap(drop_na -> bool, plot -> bool)`

Creates a heatmap of all your completed runs. The run ID is on the y-axis and the split name is on the x-axis. The color (indicated by the legend on the right side of the plot) indicates how much faster/slower that split was from the mean. Just a cool color plot to see how well your runs do :()

* `drop_na`: Whether to include rows that have missing data from your plot. The default value is set to `False`.
* `plot`: Determines whether you want to see this as a standalone graph. Setting this to `True` will cause `plt.show()` to be run. Setting this to `False` will cause `plt.show()` to not be running, allowing you to add more graphs to your plot should you want to do that. The default value is set to `True`.

## `RunnerData`

The `RunnerData` class provides functions for analyzing data between splits files. Currently, it is the responsibility of the developer to put splits files together. 

To create a `RunnerData` object, you need to create a dictionary where the keys are the usernames of each runner and the values are a `LivesplitData` object for each runner. This dictionary then gets passed into the `RunnerData` object. For example:

```python
runner1 = LivesplitData('path/to/LiveSplit/file')
runner2 = LivesplitData('path/to/Livesplit/file')

runner_dict = {'runner1username':runner1, 'runner2username':runner2}
runner_data = RunnerData(runner_dict)
```

### `RunnerData.plot_percent_past(cumulative=False -> bool)`

Creates a side-by-side barplot showing the percentage of runs that get past a certain split. Each color represents a specific runner. If cumulative is True, computes the percentages based on all attempts. If cumulative is False (default), computes the perecntages based on the number of runs that got to that specific split.

EX: In SM64 16 Star with splits BOB, WF, CCM, etc..., cumulative=True would compute the % past based on all attempts, but the % past for WF would be the percentage of runs that got past WF **of the runs that got to WF**.

Returns an altair Chart object containing the plot of the percent past.