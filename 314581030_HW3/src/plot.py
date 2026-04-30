import matplotlib.pyplot as plt
import numpy as np

def calculate_ewma(raw_rewards, alpha=0.05):
    """
    Calculate Exponentially Weighted Moving Average (EWMA) for smoothing reward curves.
    """
    ewma_corrected = []
    curr_value = 0.0 # Initial value for EWMA
    for t, val in enumerate(raw_rewards, 1):
        curr_value = alpha * val + (1 - alpha) * curr_value
        
        bias_correction = 1 - (1 - alpha) ** t
        
        ewma_corrected.append(curr_value / bias_correction)
        
    return ewma_corrected

def plot_results(rl_agent_rewards, random_rewards, la_rewards, op_name="random", eval=False):
    """
    From raw reward lists, calculate EWMA curves and plot them together.
    """
    # Ensure all reward lists have the same length for fair comparison
    if not eval:
        rl_agent_curve = calculate_ewma(rl_agent_rewards, alpha=0.05) if rl_agent_rewards is not None else None
        random_curve = calculate_ewma(random_rewards, alpha=0.05) if random_rewards is not None else None
        la_curve = calculate_ewma(la_rewards, alpha=0.05) if la_rewards is not None else None
    else:
        # For evaluation, we can plot raw rewards
        rl_agent_curve = rl_agent_rewards if rl_agent_rewards is not None else None
        random_curve = random_rewards if random_rewards is not None else None
        la_curve = la_rewards if la_rewards is not None else None

    plt.figure(figsize=(10, 6))
    m_every = max(1, len(random_curve) // 20)
    
    # Baseline: Random Agent
    if random_curve is not None:
        plt.plot(random_curve, label="Random", color='gray', linestyle='--', linewidth=1.5, alpha=0.6)
    
    # RL Agent curve
    if rl_agent_curve is not None:
        plt.plot(rl_agent_curve, label="Agent", color='#1f77b4', linestyle='-', linewidth=6, alpha=0.4)

    # L_A Agent curve    
    if la_curve is not None:
        plt.plot(la_curve, label="L_A", color='#d62728', linestyle='-', linewidth=2, 
                 marker='o', markersize=6, markevery=m_every)
    
    plt.xlabel("Episodes")
    plt.ylabel("EWMA Rewards")
    plt.title(f"{'' if eval else 'EWMA '}Rewards over Episodes for {op_name} opponent")
    plt.legend(loc='lower right', fontsize=10, framealpha=0.9)
    plt.grid(True, linestyle=':', alpha=0.8)
    plt.tight_layout()
    
    filename = f"result_{op_name}_{'eval' if eval else 'train'}.png"
    plt.savefig(filename)
    plt.close()
    print(f"store {filename}")
    
