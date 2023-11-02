import gym
from gym import spaces
import random
from mutators import *

class AFLppFuzzEnv(gym.Env):
    def __init__(self, input_maxsize, max_steps):
        super(AFLppFuzzEnv, self).__init()
        
        # Initialize environment parameters
        self.input_max_size = input_maxsize  # The maximum states we can observe
        self.max_steps = max_steps  # Maximum number of steps for an episode
        self.current_step = 0

        # Define mutation methodsm
        self.methodNum = MutationMethods.MUT_MAX

        # Define action and state spaces
        self.state_space = spaces.Discrete(input_maxsize)
        self.action_space = spaces.Discrete(self.methodNum)

        # Define initial state (seed) and coverage-related variables
        self.current_seed = None
        self.number_of_current_total_coverage = 0
        self.number_of_current_total_crash = 0
        self.number_of_caused_coverage = 0
        self.number_of_unique_crash_caused = 0

    def reset(self):
        self.number_of_unique_coverage_found = 0
        self.number_of_unique_crash_caused = 0

        # Initialize the current_seed with an initial seed
        self.current_seed = mutant  

        self.number_of_unique_coverage_found = 0
        self.number_of_unique_crash_caused = 0

        # Reset the step count
        self.current_step = 0

        return self.current_seed

    def step(self, action):
        info = self.step_raw(action)

        reward = 0.0
        done = False
        c = info['step_coverage']

        # Calculate reward based on transition count
        reward = calculate_reward()

        # Check for coverage changes
        old_path_count = self.number_of_current_total_coverage
        self.number_of_current_total_coverage += c.transition_count()
        new_path_count = self.number_of_current_total_coverage

        # Check if the episode is done (e.g., when there's no new coverage)
        if old_path_count == new_path_count:
            done = True

        # Update the environment state and provide additional info
        self.current_seed = info['input_data']
        info['total_coverage'] = self.number_of_current_total_coverage

        return self.current_seed, reward, done, info

    def calculate_reward(self, seed, method):
        prev_coverage = self.number_of_current_total_coverage
        current_coverage = self.number_of_caused_coverage
        reward = current_coverage - prev_coverage
        self.number_of_caused_coverage = current_coverage

        return reward

        