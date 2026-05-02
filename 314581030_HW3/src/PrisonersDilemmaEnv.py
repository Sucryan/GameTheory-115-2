import gymnasium as gym
from gymnasium import spaces
import numpy as np

class PrisonersDilemmaEnv(gym.Env):
    """
    Repeated Prisoner's Dilemma Environment

    Action Space (Discrete):
        0: Stay Silent (Cooperation)
        1: Betray
        
    Observation Space (Box):
        [Protagonist Last Action, Opponent Last Action]
        Def: 0=Silent, 1=Betray, -1=Initial State
        
    Rewards:
        Game Matrix (Protagonist, Opponent):
    """
    def __init__(self, opponent_type='tft', max_steps=100):
        super(PrisonersDilemmaEnv, self).__init__()
        self.max_steps = max_steps
        self.opponent_type = opponent_type
        self.current_step = 0
        
        # 0/1
        self.action_space = spaces.Discrete(2)
        
        # [Protagonist_last, Opponent_last]
        self.observation_space = spaces.Box(low=-1, high=1, shape=(2,), dtype=np.int64)
        
        # Reward function (Protagonist, Opponent)
        self.payoff_matrix = np.array([
            [(10, 10), (4,  12)],
            [( 12, 4), (6, 6)]
        ])

        self.state = np.array([-1, -1], dtype=np.int64)
        self.reward_range = (4.0, 12.0)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.current_step = 0
        self.state = np.array([-1, -1], dtype=np.int64)
        return self.state, {}

    def _get_opponent_action(self, agent_action):
        # Opponent action based on the specified strategy
        if self.opponent_type == 'rand': # Random
            return np.random.randint(2)
        
        elif self.opponent_type == 'silent': # Always_silent
            return 0
        
        elif self.opponent_type == 'betray': # Always_betrayal
            return 1
        
        elif self.opponent_type == 'tft': # Tit_for_tat
            # Initially cooperate, then mimic the agent's last action
            if int(self.state[0]) == -1:
                return 0
            # Copy the protagonist's "previous" action (i.e., the current state[0])
            return int(self.state[0])
            
        return 0 # Default fallback

    def step(self, action):
        # 1. Opponent decides action based on strategy
        try:
            action = float(action[0])
        except (TypeError, IndexError, ValueError):
            action = float(action)
        opponent_action = self._get_opponent_action(action)
        # print(f"a2 action: {opponent_action}")

        action_int = int(action)
        opponent_action = int(opponent_action)
        
        # 2. Obtain rewards
        agent_reward, opponent_reward = self.payoff_matrix[action_int, opponent_action]
        
        # 3. Update state and info
        info = {
            "opp_action": opponent_action,
            "agent_reward": agent_reward,
            "opp_reward": opponent_reward
        }
        
        # Renew state with current actions
        self.state = np.array([action_int, opponent_action], dtype=np.int64)
        self.current_step += 1
        
        # 4. Epoch termination condition
        terminated = self.current_step >= self.max_steps
        truncated = False
        
        return self.state, float(agent_reward), terminated, truncated, info

    def render(self):
        # Just testing: Print the last actions of both agents
        act_map = {-1: "Start", 0: "Silent", 1: "Betray"}
        agent_last = act_map[self.state[0]]
        opp_last = act_map[self.state[1]]
        print(f"Step {self.current_step}: Last State -> Agent: {agent_last}, Opponent: {opp_last}")
