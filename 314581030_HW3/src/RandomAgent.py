from BaseAgent import BaseAgent

import numpy as np


class RandomAgent(BaseAgent):
    def __init__(self, env, total_episodes=300):
        super().__init__(env, total_episodes)  # Parent class initialization

    def act(self, state, explore):
        return self.action_space.sample() # Just randomly sample an action from the action space
        
    def update(self, obs, action, reward, next_obs, done):
        pass # w/o any learning mechanism

    def save_model(self, name="model_name"):
        print("RandomAgent has no model to save.")
        pass

    def load_model(self, name="model_name"):
        print("RandomAgent has no model to load.")
        pass
