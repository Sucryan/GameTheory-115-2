from BaseAgent import BaseAgent

import numpy as np

class LAAgent(BaseAgent):
    def __init__(self, env, total_episodes=300, alpha=0.1, rho=0.05, initial_p_c=0.5, pure_binary=False): 
        super().__init__(env, total_episodes)  # Parent class initialization
        self.alpha = alpha                     # Reward step size
        self.rho = rho                         # Penalty step size, rho = 0
        self.p_C = initial_p_c                 # Initial probability of cooperating (stay silent)
        
        # For pure_binary version
        self.eta = 0.1            # Smoothing constant for running average of rewards 
        self.R_bar = 0.0          # Running Average
        self.is_first_step = True # The starting point of the running average, will be set to False after the first step
        self.pure_binary = pure_binary

    def act(self, state, explore):
        # Based on the current probability of cooperating (p_C), decide whether to cooperate (stay silent) or betray
        # 0 is cooperation (Stay Silent), 1 is Betray
        if np.random.rand() < self.p_C:
            return 0 
        else:
            return 1
    
    def save_model(self, name="la_agent_pC.npy"):
        # L_RP Agent just needs to save its probability of cooperating (p_C) as the model
        if self.rho == 0.0:
            name = f"lri_{name}"
        else:
            name = f"lrp_{name}"
        np.save(name, self.p_C)
        print("Training completed. Writing model to "+name)

    def load_model(self, name="la_agent_pC.npy"):
        if self.rho == 0.0:
            name = f"lri_{name}"
        else:
            name = f"lrp_{name}"
        self.p_C = np.load(name)
        print("Reading model from "+name)
    
    def update(self, obs, action, reward, next_obs, done):
        """
        Update function
        """

        # How to determine beta for pure_binary version or continuous version:
        # For pure_binary version, we use the running average of rewards (R_bar) to determine success or failure
        # For continuous version, we use the min and max payoff to determine beta
        beta = 

        # L_RP/L_RI Update Rule
        if action == 0: 
            # Selected cooperation (silent), update p_C accordingly
            self.p_C = 
        else:
            # Selected betrayal, how to update p_C?


        # clip p_C to [0, 1] to ensure it's a valid probability
        self.p_C = np.clip(self.p_C, 0.0, 1.0)

        # Update the running average of rewards (R_bar) if you need it for the pure_binary version
        # R_{k+1} = (1 - η) * R_k + η * r(k)
        # self.R_bar = 