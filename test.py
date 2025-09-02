from livesplit_parser.livesplit_data import LivesplitData
from livesplit_parser.runner_data import RunnerData
import matplotlib as plt

frobuddy = LivesplitData('frobuddy_sm64_16star.lss', time_key="RealTime")
super64guy = LivesplitData('super64guy_sm64_16star.lss', time_key="RealTime")
test_dict = RunnerData({'super64guy':super64guy, 'frobuddy':frobuddy})

fig = test_dict.plot_num_attempts_comp()

