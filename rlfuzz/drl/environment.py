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
        if self.current_step >= self.max_steps:
            return self.current_seed, 0, True, {}
      
        selected_method = MutationMethods(random.randint(0, MutationMethods.MUT_MAX - 1))
        mutated_seed = self.mutate_seed(self.current_seed, selected_method)

        self.current_seed = mutated_seed

        reward = self.calculate_reward(self.current_seed, selected_method)

        # Increment the step count
        self.current_step += 1

        # Check if the episode is done
        done = self.current_step >= self.max_steps

        return self.current_seed, reward, done, {}

    def mutate_seed(self, seed, method):
        # Apply the AFL++ mutation method to the testcase.
        # Return the mutated testcase.
        pass

    def calculate_reward(self, seed, method):
        prev_coverage = self.number_of_current_total_coverage
        current_coverage = self.number_of_caused_coverage
        reward = current_coverage - prev_coverage
        self.number_of_caused_coverage = current_coverage

        return reward

        