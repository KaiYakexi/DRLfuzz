import gym
from gym import spaces
import random
from mutators import *

in_fifo_file = 'fifo1'
out_fifo_file = 'fifo2'
in_fifo_fd = None
out_fifo_fd = None

def open_pipe(in_fifo = in_fifo_file, out_fifo = out_fifo_file):
    in_fifo_fd = open(in_fifo_file, 'rb')
    out_fifo_fd = open(out_fifo_file, 'wb')
    
def send_mutation(mutation, fd = out_fifo_fd):
    send_bytes = mutation.to_bytes(4, 'little')
    fd.write(send_bytes)
    fd.flush()

def recv_reward_testcase(fd = in_fifo_file):
    head = fd.read(13)
    coverage = int.from_bytes(head[:4], 'little')
    edge = int.from_bytes(head[4:5], 'little')
    crash = int.from_bytes(head[5:9], 'little')
    length = int.from_bytes(head[9:13], 'little')
    testcase = fd.read(length) #bytes #tensor
    zero_length = 4096 - length
    testcase = testcase + b'\x00' * zero_length
    #testcase = list(map(int, testcase))
    return (coverage, edge, crash, testcase)

class AFLppFuzzEnv(gym.Env):
    def __init__(self, input_maxsize, max_steps):
        super(AFLppFuzzEnv, self).__init()
        
        # Initialize environment parameters
        self.input_max_size =  # The maximum states we can observe
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
        coverage, edge, crash, testcase = self.recv_reward_testcase()
        self.current_seed = testcase

        self.number_of_unique_coverage_found = 0
        self.number_of_unique_crash_caused = 0

        # Reset the step count
        self.current_step = 0

        return self.current_seed

    def step(self, action):
        new_state = 


        done = self.current_step >= self.max_steps

        return self.current_seed, reward, done, info

    def render(self, mode='human', close=False):
        pass

    def eof(self):
        return self._dict.eof()

    def dict_size(self):
        return self._dict.size()

    def input_size(self):
        return self._input_size
        