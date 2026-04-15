import random
import matplotlib.pyplot as plt
import pandas as pd
# 初始設定：
epsilon = 1e-6
MAX_ITER = 2000000
initial_priors = [
    [1, 0], # 必出 A
    [0, 1], # 必出 B
    [1, 1]  # 50% 50%
]

# mat: 0:左上角, 1左下, 2右下, 3右上
# mat[x]: 0: Player1, 1: Player2
# mat: 0:左上角(r1,c1), 1:左下角(r2,c1), 2:右下角(r2,c2), 3:右上角(r1,c2)
# mat[x]: 0: Player1, 1: Player2
Q_all = [
    # Q1
    [
        [-1, -1],
        [0, 1],
        [3, 3],
        [1, 0]
    ],
    # Q2
    [
        [2, 2],
        [0, 1],
        [3, 3],
        [1, 0]
    ],
    # Q3
    [
        [1, 1],
        [0, 0],
        [0, 0],
        [0, 0]
    ],
    # Q4
    [
        [0, 1],
        [2, 0],
        [0, 4],
        [2, 0]
    ],
    # Q5
    [
        [0, 1],
        [1, 0],
        [0, 1],
        [1, 0]
    ],
    # Q6
    [
        [10, 10],
        [0, 0],
        [10, 10],
        [0, 0]
    ],
    # Q7
    [
        [0, 0],
        [1, 1],
        [0, 0],
        [1, 1]
    ],
    # Q8
    [
        [3, 2],
        [0, 0],
        [2, 3],
        [0, 0]
    ],
    # Q9
    [
        [3, 3],
        [2, 0],
        [1, 1],
        [0, 2]
    ]
]

def plot_convergence(history, q_idx, p1_init, p2_init):
    # 提取歷史紀錄
    rounds = [h['round'] for h in history]
    p1_probs = [h['prev_p1_0'] for h in history]
    p2_probs = [h['prev_p2_0'] for h in history]
    
    plt.figure(figsize=(10, 5))
    plt.plot(rounds, p1_probs, label="Player 1 Prob (r1)", color='#1f77b4', linewidth=2)
    plt.plot(rounds, p2_probs, label="Player 2 Prob (c1)", color='#ff7f0e', linewidth=2)
    
    # 圖表美化
    title = f"Q{q_idx+1} Convergence (P1 Init:{p1_init}, P2 Init:{p2_init})"
    plt.title(title, fontsize=14, fontweight='bold')
    plt.xlabel("Iteration (Rounds)", fontsize=12)
    plt.ylabel("Probability of Action 1", fontsize=12)
    plt.ylim(-0.05, 1.05) # 機率範圍 0~1
    plt.legend(loc='best')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    # 存檔 (檔名會自動帶入題號與初始狀態)
    filename = f"Q{q_idx+1}_P1_{p1_init[0]}{p1_init[1]}_P2_{p2_init[0]}{p2_init[1]}.png"
    plt.savefig(filename, dpi=150)
    plt.close() # 關閉畫布避免記憶體爆掉

def generate_summary_table(q_idx, results_list):
    # results_list 是一個 list，裡面裝了這題 9 種組合的結果
    df = pd.DataFrame(results_list)
    
    print(f"\n{'='*20} Question {q_idx+1} Summary {'='*20}")
    # 在終端機印出精美表格
    print(df.to_string(index=False))
    
    # 如果你想把表格存成 csv 給報告用，可以取消下面這行的註解
    # df.to_csv(f"Q{q_idx+1}_summary.csv", index=False)
    
    # 甚至可以直接輸出 Markdown 格式
    # print("\nMarkdown 格式 (可直接貼上筆記軟體):")
    # print(df.to_markdown(index=False))

def experiment(prior1, prior2, Q):
    it_count = 0
    prev_p1_0 = -1
    prev_p2_0 =  -1
    history = []
    while it_count < MAX_ITER \
        and (abs(prev_p1_0-(prior1[0]/sum(prior1))) > epsilon \
            or abs(prev_p2_0-(prior2[0]/sum(prior2))) > epsilon):
        prev_p1_0 = prior1[0]/sum(prior1)
        prev_p2_0 = prior2[0]/sum(prior2)
        history.append({
            "round": it_count,
            "prev_p1_0": prev_p1_0,
            "prev_p2_0": prev_p2_0
        })
        # expect value of P1, P2
        E_P1, E_P2 = [0, 0], [0, 0]
        E_P1[0] = prior2[0]*Q[0][0]+prior2[1]*Q[3][0]
        E_P1[1] = prior2[0]*Q[1][0]+prior2[1]*Q[2][0]
        E_P2[0] = prior1[0]*Q[0][1]+prior1[1]*Q[1][1]
        E_P2[1] = prior1[0]*Q[3][1]+prior1[1]*Q[2][1]
        # 計算哪個好，好的那個動作就多做一次，如果一樣好就取隨機。
        if E_P1[0] > E_P1[1]:
            prior1[0] += 1
        elif E_P1[0] < E_P1[1]:
            prior1[1] += 1
        else:
            if (random.random() < 0.5):
                prior1[0] += 1
            else:
                prior1[1] += 1
        if E_P2[0] > E_P2[1]:
            prior2[0] += 1
        elif E_P2[0] < E_P2[1]:
            prior2[1] += 1
        else:
            if (random.random() < 0.5):
                prior2[0] += 1
            else:
                prior2[1] += 1
        it_count += 1 
    return prev_p1_0, prev_p2_0, history

# 九個問題
for it in range(9):
    # prior1, prior2個三種init
    q_results = []
    for i in range(3):
        for j in range(3):
            history = []
            final_p1_0, final_p2_0, history = experiment(list(initial_priors[i]), list(initial_priors[j]), Q_all[it])
            #plot_convergence(history, it, initial_priors[i], initial_priors[j])
            q_results.append({
                "P1_Init": str(initial_priors[i]),
                "P2_Init": str(initial_priors[j]),
                "Iters": len(history),
                "P1_Final_Prob(r1)": round(final_p1_0, 4),
                "P2_Final_Prob(c1)": round(final_p2_0, 4),
            })
    generate_summary_table(it, q_results)