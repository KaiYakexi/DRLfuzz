import gym
import numpy as np
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense, LSTM
from tensorflow.keras.optimizers import Adam
from environment import AFLppFuzzEnv


# Define hyperparameters
learning_rate = 0.001
discount_rate = 0.99
batch_size = 32
epsilon_initial = 1.0
epsilon_decay = 0.995
epsilon_min = 0.01
target_update_freq = 1000  # Update target network every N steps
max_episodes = 3

env = AFLppFuzzEnv()
state_size = env.observation_space.shape[0]

class DDQN_Agent:
    def __init__(self, state_size, action_size):
        self.state_size = state_size
        self.action_size = action_size
        self.memory = []  # Use a list as a simple replay memory
        self.epsilon = epsilon_initial
        self.dqn_model = self.create_model(learning_rate, "DQN")
        self.target_dqn_model = self.create_model(learning_rate, "Target_DQN")
        self.update_counter = 0

    #NN model approximating Q-value
    def create_model(self, lr, name):
        inputs = Input(shape=(self.state_size,))
        mlp1 = Dense(64, activation='relu', kernel_initializer='he_uniform')(inputs)
        mlp2 = Dense(64, activation='relu', kernel_initializer='he_uniform')(mlp1)
        lstm = LSTM(64, activation='tanh', return_sequences=True, kernel_initializer='glorot_uniform')(mlp2)
        outputs = Dense(self.env.action_space.n, activation='linear', kernel_initializer='he_uniform')(lstm)
        model = Model(inputs=inputs, outputs=outputs, name=name)
        model.compile(loss='mse', optimizer=Adam(lr=lr))
        return model
    
    #Update target DAN with weights from current DQN
    def hard_update_target_network(self):
        self.target_dqn_model.set_weights(self.dqn_model.get_weights())  

    #Learn from a mini-batch of experiences
    def learn(self):
        #sample memory for replay
        batch = self.memory.sample(self.batch_size)
        states = [experience[0] for experience in batch]
        actions = [experience[1] for experience in batch]        
        rewards = [experience[2] for experience in batch]
        next_states = [experience[3] for experience in batch]
        dones = [experience[4] for experience in batch]

        states = np.reshape(states, [self.batch_size, self.state_size])
        next_states = np.reshape(next_states, [self.batch_size, self.state_size])

        #Use dqn model to predict Q-value of current states in mini-batch
        q_states = self.dqn_model.predict(states)

        #Use dqn model to predict Q-value of next states in mini-batch
        q_next_states = self.dqn_model.predict(next_states)
        
        #Use target dqn model to predict target Q-value of next states in mini-batch
        q_target_next_states = self.target_dqn_model.predict(next_states)

        q_optimal = q_states
        
        for i in range(self.batch_size):
            if dones[i]:
                #for terminal states target is immediate reward 
                #in current time step                 
                q_optimal[i][actions[i]] = rewards[i]
            else:
                #current dqn model determines greedy action 
                max_next_action = np.argmax(q_next_states[i])
                
                #Use Q-Value of maximal action obtained from target dqn as 
                #Q-Value target estimate
                #update rule: 𝑞(𝑠, 𝑎) += 𝛼(𝑅+ 𝑚𝑎𝑥𝑎′ 𝑞(𝑠′, 𝑎′)− 𝑞(𝑠, 𝑎))
                q_optimal[i][actions[i]] = rewards[i] + \
                   self.discount_rate * (q_target_next_states[i][max_next_action])

        #train DQN model            
        self.dqn_model.fit(states, q_optimal, batch_size = self.batch_size,
                       epochs=1, verbose=0)            
        
    def train(self, max_episodes):
        for e in range(max_episodes):
            done = False
            episode_total = 0
            state = env.reset()

            while not done:
                 #get next action following behaviour policy 
                 action = self.epsilon_greedy_action(np.reshape(state, [1, self.state_size]))

                 #interact with environment   
                 next_state, reward, done, info = env.step(action)

                 #append experience to replay memory
                 self.memory.append((state, action, reward, next_state, done))
                
                 #exploration deacy 
                 if self.epsilon > self.epsilon_min:
                    self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
                                       
                 if len(self.memory.buffer) >= 1000:
                    #train the DQN model 
                    self.learn()
                    
                 episode_total += reward
                 state = next_state

            self.hard_update_target_network()

# Main training loop
if __name__ == "__main__":
    agent = DDQN_Agent(state_size, env.action_space.n)
    
    for episode in range(max_episodes):
        state = env.reset()
        total_reward = 0

        while True:
            # Choose an action using epsilon-greedy policy
            action = agent.epsilon_greedy_action(state)

            # Interact with the environment
            next_state, reward, done, _ = env.step(action)

            # Store the experience in the replay memory
            agent.memory.append((state, action, reward, next_state, done))

            # Update the DQN model if there are enough samples in the memory
            if len(agent.memory) >= batch_size:
                agent.learn()

            total_reward += reward
            state = next_state

            if done:
                break

        # Update the target network every target_update_freq episodes
        if episode % target_update_freq == 0:
            agent.hard_update_target_network()

        # Decrease epsilon for exploration
        agent.epsilon = max(agent.epsilon * epsilon_decay, epsilon_min)

        # Print episode statistics
        print(f"Episode: {episode + 1}, Total Reward: {total_reward}")

    # Save trained models' weights if needed
    agent.dqn_model.save("dqn_model.h5")
    agent.target_dqn_model.save("target_dqn_model.h5")

# Close the environment
env.close()