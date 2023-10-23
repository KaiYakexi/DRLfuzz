import gym
from gym import spaces
import gym
from gym import spaces
import datetime
import os
import numpy as np
import xxhash
import random
from configparser import ConfigParser

import coverage as coverage
from coverage import PATH_MAP_SIZE
from mutators import *

class FuzzBaseEnv(gym.Env):
    def __init__(self):
        # Classes that inherit FuzzBase must define before calling this
        self.engine = coverage.Afl(self._target_path, args=self._args)
        self.input_maxsize = self._input_maxsize 
        self.mutator = FuzzMutatorPlus(self.input_maxsize)  
        self.mutate_size = self.mutator.methodNum  
        self.density_size = 256 # [0, 255] 
        self.input_dict = {}  
        self.covHash = xxhash.xxh64() 

        self.observation_space = spaces.Box(0, 255, shape=(self.input_maxsize,), dtype='uint8')  

        
        self.action_space = spaces.Discrete(self.mutate_size)



        self.last_input_data = b'' 
        self.input_len_history = []  
        self.mutate_history = []  
        self.reward_history = [] 
        self.unique_path_history = [] 
        self.transition_count = [] 
        
        self.virgin_count = [] 

        
        self.virgin_map = np.array([255] * PATH_MAP_SIZE, dtype=np.uint8)

        
        self.virgin_single_count = 0

        
        self.virgin_multi_count = 0

        
        self.POC_PATH = r'/tmp'
        cfg = ConfigParser()
        if cfg.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')):
            self.POC_PATH = cfg.get('PATH', 'POC_PATH')

        self.reset()

    
    def DiscreteEnv(self):
        self.mutator = FuzzMutator(self.input_maxsize)
        self.action_space = spaces.Discrete(self.mutate_size)
    
 
    def reset(self):
        self.last_input_data = self._seed
        self.input_dict = {}
        self.virgin_map = np.array([255] * PATH_MAP_SIZE, dtype=np.uint8)
        self.virgin_single_count = 0
        self.virgin_multi_count = 0

      
        self.input_maxsize = self._input_maxsize 
        
        self.mutator = FuzzMutator(self.input_maxsize)
        self.observation_space = spaces.Box(0, 255, shape=(self.input_maxsize,), dtype='int8')  # 更新状态空间（set_seed后需要修改）

        # clear all
        self.input_len_history = []  
        self.mutate_history = []  
        self.reward_history = [] 
        self.unique_path_history = [] 
        self.transition_count = [] 
        self.virgin_count = []

        assert len(self.last_input_data) <= self.input_maxsize
        return list(self.last_input_data) + [0] * (self.input_maxsize - len(self.last_input_data))
    
    def actor2actual(self, output, scale):
        return int(output * np.ceil(scale/2) + np.ceil(scale/2)) % scale

    
    def updateVirginMap(self, covData):
        res = False
        for i in range(PATH_MAP_SIZE):
            if covData[i] and covData[i] & self.virgin_map[i]: 
                if self.virgin_map[i] == 255:
                    self.virgin_single_count += 1 
                res = True
                self.virgin_map[i] &= ~(covData[i])
                self.virgin_multi_count += 1 
        return res

    def step_raw(self, action):
        if self.action_space.contains(action):
            mutate = action
        else:
            mutate = np.argmax(action)
        assert self.action_space.contains(mutate)
        input_data = self.mutator.mutate(mutate, self.last_input_data)

        
        self.mutate_history.append(mutate)

        
        self.input_len_history.append(len(input_data))

        
        self.coverageInfo = self.engine.run(input_data)

        
        self.covHash.reset()
        self.covHash.update(self.coverageInfo.coverage_data.tostring())
        tmpHash = self.covHash.digest()
        # if tmpHash not in list(self.input_dict): 
        if self.updateVirginMap(self.coverageInfo.coverage_data):
            self.input_dict[tmpHash] = input_data
            self.last_input_data = input_data
        else: 
            self.last_input_data = self.input_dict[random.choice(list(self.input_dict))]

        self.virgin_count.append([self.virgin_single_count, self.virgin_multi_count]) 
        self.unique_path_history.append(len(self.input_dict)) 

        
        self.transition_count.append(self.coverageInfo.transition_count())

        return {
            "reward": self.coverageInfo.reward(),
            "input_data": input_data,
            "crash_info": True if self.coverageInfo.crashes > 0 else False 
        }

    def step(self, action):

        info = self.step_raw(action)
        reward = info['reward']
        assert reward <= 1

        if info['crash_info']:
            # reward = 1 # adjust reward
            done = True
            name = '{}-{}'.format(os.path.basename(self._target_path), datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S.%f')) 
            print(' [+] Find {}'.format(name))
            with open(os.path.join(self.POC_PATH, name), 'wb') as fp:
                fp.write(info['input_data'])
        else:
            done = False

        
        self.reward_history.append(reward)

        
        state = [m for m in info['input_data']]
        trail = [0] * (self.input_maxsize - len(state))
        state += trail

        assert len(state) == self.input_maxsize, '[!] len(state)={}, self.input_maxsize={}'.format(len(state), self.input_maxsize)

        return state, reward, done, {}

    def render(self, mode='human', close=False):
        pass

    def eof(self):
        return self._dict.eof()

    def dict_size(self):
        return self._dict.size()

    def input_size(self):
        return self.input_maxsize

    def get_poc_path(self):
        return self.POC_PATH