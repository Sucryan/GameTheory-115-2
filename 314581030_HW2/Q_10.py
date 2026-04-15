import random
import matplotlib.pyplot as plt

# MAX_ITER 跑個超級大的100萬次
MAX_ITER = 1000000

# Shapley's Polygon (3x3 Matrix)
# 格式: mat[r][c] = (P1_payoff, P2_payoff)
Q_Shapley = [
    [(0,0), (1,0), (0,1)],
    [(0,1), (0,0), (1,0)],
    [(1,0), (0,1), (0,0)]
]

# 為了證明不管怎麼起手都不會收斂，設定三組不同的初始狀態
# 格式: (P1_prior, P2_prior)
initial_priors_3x3 = [
    ([1, 0, 0], [0, 1, 0]), # 偏向某個純策略
    ([0, 1, 0], [0, 0, 1]), # 另一種錯開的純策略
    ([1, 1, 1], [1, 1, 1])  # 大家一開始都很公平 (1/3, 1/3, 1/3)
]

def experiment_3x3(prior1, prior2, Q, max_iter):
    it_count = 0
    history = []
    
    # 因為我們知道它不會收斂，所以不設 epsilon 條件，直接跑到 max_iter 撞牆
    while it_count < max_iter:
        p1_probs = [p/sum(prior1) for p in prior1]
        p2_probs = [p/sum(prior2) for p in prior2]
        
        history.append({
            "round": it_count,
            "p1_prob": list(p1_probs),
            "p2_prob": list(p2_probs)
        })
        
        # expect value of P1, P2
        E_P1 = [0, 0, 0]
        E_P2 = [0, 0, 0]
        
        for i in range(3): # P1 action
            for j in range(3): # P2 action
                E_P1[i] += prior2[j] * Q[i][j][0]
                E_P2[j] += prior1[i] * Q[i][j][1]
                
        # Best response for P1 (如果有一樣大的就隨機挑)
        max_p1 = max(E_P1)
        best_p1 = [i for i, x in enumerate(E_P1) if x == max_p1]
        action_p1 = random.choice(best_p1)
        
        # Best response for P2 (如果有一樣大的就隨機挑)
        max_p2 = max(E_P2)
        best_p2 = [i for i, x in enumerate(E_P2) if x == max_p2]
        action_p2 = random.choice(best_p2)

        prior1[action_p1] += 1
        prior2[action_p2] += 1
        
        it_count += 1 
        
    return history

def plot_shapley():
    plt.figure(figsize=(12, 8))
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    styles = ['-', '--', ':']
    
    # 跑三種不同的初始狀態，把線畫在同一張圖上
    for idx, (p1_init, p2_init) in enumerate(initial_priors_3x3):
        # 記得用 list 複製
        history = experiment_3x3(list(p1_init), list(p2_init), Q_Shapley, MAX_ITER)
        
        rounds = [h['round'] for h in history]
        
        # 為了圖表乾淨，我們只畫出 Player 1 選擇第一招 (r1) 的機率變化
        p1_action0_probs = [h['p1_prob'][0] for h in history]
        
        label_text = f"P1 Init:{p1_init}, P2 Init:{p2_init}"
        plt.plot(rounds, p1_action0_probs, label=label_text, color=colors[idx], linestyle=styles[idx], alpha=0.8, linewidth=1.5)

    # 圖表美化
    plt.title("Fictitious Play on Shapley's Polygon (3x3 Matrix)", fontsize=16, fontweight='bold')
    plt.xlabel("Iteration (Rounds)", fontsize=14)
    plt.ylabel("Probability of Action 1 for Player 1", fontsize=14)
    plt.ylim(-0.05, 1.05)
    
    # 畫上納許均衡的理論值 (1/3)
    plt.axhline(y=1/3, color='r', linestyle='-.', alpha=0.5, label="Nash Equilibrium (1/3)")
    
    plt.legend(loc='upper right')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig('shapley_convergence.png', dpi=150)
    print("Q10 Image Saved as shapley_convergence.png")

if __name__ == "__main__":
    plot_shapley()