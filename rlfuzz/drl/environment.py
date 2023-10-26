import gym
from gym import spaces



class AFLppFuzzEnv(gym.Env):
    def __init__(self): 
        super(AFLppFuzzEnv, self).__init__()

        
        self.input_max_size = input_maxsize # the maximum states we can observed
        
        # mutation methods
        self.mutate_map = {0: self.Mutate_EraseBytes,
                           1: self.Mutate_InsertByte,
                           2: self.Mutate_InsertRepeatedBytes,
                           3: self.Mutate_ChangeByte,
                           4: self.Mutate_ChangeBit,
                           5: self.Mutate_ShuffleBytes,
                           6: self.Mutate_ChangeASCIIInteger,
                           7: self.Mutate_ChangeBinaryInteger,
                           8: self.Mutate_CopyPart,
                           9: self.Mutate_Random,
                           10: self.Mutate_AddWordFromManualDictionary}
        self.methodNum = len(self.mutate_map)

        self.state_space = spaces.Discrete(input_maxsize)
        self.action_space = spaces.Discrete(len(self.mutate_map))
        self.max_seed_len = 2**16

        self.number_of_current_total_coverage = 0
        self.number_of_current_total_crash = 0
        self.number_of_unique_coverage_found = 0
        self.number_of_unique_crash_caused = 0

    def reset(self):
        self.number_of_unique_coverage_found = 0
        self.number_of_unique_crash_caused = 0

        self.state_space = spaces.Discrete(input_maxsize)
        self.action_space = spaces.Discrete(len(self.mutate_map))

        self.number_of_unique_coverage_found = 0
        self.number_of_unique_crash_caused = 0

        return 0

    def step(self, action):

        pass

   
        