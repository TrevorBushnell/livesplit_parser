# Livesplit-Parser

#### A Python Package to Parse Your Data Regarding Your Speedruns

This Pyton package parses LiveSplit files and parses data within LiveSplit files.

As of the 0.1 release, the only module included is the `LivesplitData` class, which neatly bundles all data inside your LiveSplit file into one object. The attributes are as follows:

* `LivesplitData.num_attempts`: the number of attempts for your run
* `LivesplitData.num_completed_attempts`: the number of attempts that were also completed runs
* `LivesplitData.percent_runs_completed`: the percentage of all your attempts that were completed (this is just `LivesplitData.num_completed_attempts / LivesplitData.num_attempts * 100`)
* `LivesplitData.attempt_info_df`: A `pandas.DataFrame` object containing information about every attempt. Each row is an attempt indexed by an ID. The columns of the dataframe are as follows:
  * `started`: timestamp of when the attempt started
  * `isStartedSynced`: ?????
  * `ended`: timestamp of when the attempt ended
  * `isEndedSynced`: ?????
  * `RunCompleted`: If `True`, the attempt was a completed run. If `False`, the attempt was not a completed run
  * `RealTime`: If not a completed run, shows the time the attempt lasted for. If a completed run, shows the final time of the run.
  * Every column afterwards is the name of a split and the length of that segment for that attempt
* `LiveSplitData.split_info_df`: A `pandas.DataFrame` object containing general information about every segment in your run. Each row is an individual split in your run. The columns of the dataframe are as follows:
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


## Example Usage

```python
from livesplit_parser import LivesplitData

lss_path = '' # put the path to your .lss file here
my_run = LivesplitData(lss_path)

print('NUMBER OF ATTEMPTS:', my_run.num_attempts)
print('NUMBER OF COMPLETED ATTEMPTS:', my_run.num_completed_attempts)
print('PERCENTAGE OF RUNS COMPLETED:', my_run.percent_runs_completed)
print('YOUR ATTEMPT DATA\n:', my_run.attempt_info_df)
print('YOUR SPLIT DATA:\n', my_run.split_info_df)
```
