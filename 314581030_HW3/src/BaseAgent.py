# base_agent.py
class BaseAgent:
    def __init__(self, env, total_episodes=300):
        self.env = env
        self.total_episodes = total_episodes
        self.action_space = env.action_space

    def act(self, state, explore):
        """
        state: observation from the environment
        explore: whether to explore or exploit
        """
        raise NotImplementedError

    def update(self, obs, action, reward, next_obs, done):
        """
        Update the agent's knowledge based on the transition (obs, action, reward, next_obs, done)
        """
        raise NotImplementedError
    
    def save_model(self, name="model_name"):
        """
        model_name: .npy, .pt, .pth, .json
        """
        raise NotImplementedError
    
    def load_model(self, name="model_name"):
        """
        model_name: .npy, .pt, .pth, .json
        """
        raise NotImplementedError