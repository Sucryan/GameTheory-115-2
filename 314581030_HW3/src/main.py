# main_evaluator.py
import numpy as np
import random
import torch
from PrisonersDilemmaEnv import PrisonersDilemmaEnv
from plot import plot_results

from RandomAgent import RandomAgent


# Please uncomment the following lines when you have completed LAAgent
from LAAgent import LAAgent
# You might also need to import your RL agent and import 
# import statements for your RL agent here
from RLAgent import RLAgent


def run_simulation(env, agent, episodes=300, is_eval=False):
    """
    Unified simulation loop for both training and evaluation.
    """
    all_rewards = []
    
    for ep in range(1, episodes + 1):
        obs, _ = env.reset()
        done = False
        episode_reward = 0.0
        
        while not done:
            # 1. choose action
            action = agent.act(obs, explore=not is_eval)
            
            # 2. interact with environment
            next_obs, reward, terminate, truncate, _ = env.step(action)
            done = terminate or truncate
            
            # 3. call agent update (only if training)
            if not is_eval:
                agent.update(obs, action, reward, next_obs, done)
                
            obs = next_obs
            episode_reward += reward
            
        all_rewards.append(episode_reward)
        
    return all_rewards

if __name__ == "__main__":
    fix_seed = 2021
    OPPONENT = ["tft", "rand", "silent", "betray"]
    TRAIN_EPISODES = 400
    EVAL_EPISODES = 100
    
    for op in OPPONENT:
        random.seed(fix_seed)
        torch.manual_seed(fix_seed)
        np.random.seed(fix_seed)
        torch.cuda.manual_seed(fix_seed) #
        
        print(f"\n=== Opponent: {op} ===")
        env = PrisonersDilemmaEnv(opponent_type=op)
        env.action_space.seed(fix_seed)
        env.observation_space.seed(fix_seed)

        print("=== Start Training ===")
        agent_rand = RandomAgent(env, total_episodes=TRAIN_EPISODES)
        # Initialize your RL agent here, e.g. agent_rl = YourRLAgent(env, total_episodes=TRAIN_EPISODES)
        agent_rl = RLAgent(env, total_episodes=TRAIN_EPISODES, seed=fix_seed)
        # Remove None and uncomment the following line to initialize your LA agent
        agent_la = LAAgent(env, total_episodes=TRAIN_EPISODES, rho=0.05)
        
        train_rewards_rand = run_simulation(env, agent_rand, TRAIN_EPISODES, is_eval=False)
        # Remove None and execute your RL agent to train and obtain rewards
        train_rewards_rl = run_simulation(env, agent_rl, TRAIN_EPISODES, is_eval=False)
        # Remove None and uncomment the following line to let your LA agent learn and collect rewards
        train_rewards_la = run_simulation(env, agent_la, TRAIN_EPISODES, is_eval=False)
        


        print("=== Start Evaluation ===")
        eval_rewards_rand = run_simulation(env, agent_rand, EVAL_EPISODES, is_eval=True)
        # Remove None and uncomment the following line for your RL agent to evaluate and obtain rewards via the same eval loop
        eval_rewards_rl = run_simulation(env, agent_rl, EVAL_EPISODES, is_eval=True)
        # Remove None and uncomment the following line to evaluate your LA agent via the same eval loop
        eval_rewards_la = run_simulation(env, agent_la, EVAL_EPISODES, is_eval=True)

        
        print("=== Plotting Graphs ===")
        # Plotting results with EWMA for training rewards to show trends, and raw rewards for evaluation
        # With unified plotting function, we can easily compare all agents under the same opponent
        plot_results(train_rewards_rl,  train_rewards_rand, train_rewards_la, op_name=op, eval=False)
        plot_results(eval_rewards_rl,  eval_rewards_rand, eval_rewards_la, op_name=op, eval=True)
