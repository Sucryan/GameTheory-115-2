# HW1 Graph Game 專案說明

## 1. Project Overview

本專案是 Game Theory HW1 的程式實作與實驗工具集合，核心目標是：

1. 讀入以 bit-string adjacency matrix 表示的圖
2. 在同一張圖上執行三個 graph game solver
3. 輸出三題對應結果的 cardinality
4. 額外提供 WS graph 測資生成與 checker/benchmark 工具，協助驗證與分析

三個問題目前對應如下：

1. Problem 1-1: MIS-bas ed IDS Game  
目標是透過 best-response dynamics 收斂到合法 IDS（Independent Dominating Set），並在 multi-start 結果中取較小 cardinality。

2. Problem 1-2: Symmetric MDS-based IDS Game  
使用對稱版效用函數（含 domination gain、activation cost、independence penalty）做 best-response dynamics，同樣希望得到合法 IDS，並取較小 cardinality。

3. Problem 2: Matching Game  
每個節點選擇配對對象或不提案，透過 best-response dynamics 找到合法且 maximal 的 matching，並在 multi-start 結果中取較大 matching cardinality。

WS model 的用途：

- 生成可控參數的圖測資（n, k, p）
- 讓 solver 在不同圖結構與 rewiring 程度下測試
- 供 checker 做批次 benchmark 與繪圖分析

---

## 2. File Structure

- [314581030_HW1/src/314581030_HW1_main.py](314581030_HW1/src/314581030_HW1_main.py)  
  主程式。負責輸入解析、建圖、執行三個 solver、輸出三題 cardinality。

- [314581030_HW1/src/ws_generator.py](314581030_HW1/src/ws_generator.py)  
  WS graph 生成器。可輸出作業格式資料，也可直接呼叫主程式做 smoke run。

- [314581030_HW1/src/checker.py](314581030_HW1/src/checker.py)  
  驗證與 benchmark 工具。會動態載入主程式中的 solver，檢查合法性、NE 指標、maximal matching 指標，並輸出表格與圖檔。  
  這不是交作業主程式的一部分，而是開發與實驗輔助工具。

- [314581030_HW1/src/test_minimum.py](314581030_HW1/src/test_minimum.py)  
  最小化 smoke test。只檢查給定 sample case 是否能跑通與輸出關鍵字串。  
  目前測試覆蓋率很有限（檔案內也有 TODO 註記）。

- [314581030_HW1/src/checker_outputs](314581030_HW1/src/checker_outputs)  
  checker 預設輸出圖檔資料夾。

---

## 3. Input / Output Format

### 3.1 主程式輸入格式

主程式 CLI 目前格式為：

    python3 314581030_HW1_main.py n row1 row2 ... rowN

其中：

- n: 節點數（正整數）
- rowi: 長度為 n 的 01 字串，代表 adjacency matrix 第 i 列

目前已做的輸入檢查：

- n 必須大於 0
- bit-string 列數必須剛好是 n
- 每列長度必須是 n
- 每個字元只能是 0 或 1

目前仍保留的保守註記（TODO）：

- 是否強制無向圖（矩陣對稱）尚未在 validate_input_format 強制檢查
- 是否強制對角線為 0（無 self-loop）尚待依作業規範最終確認

### 3.2 主程式輸出格式

主程式會印出三段結果，格式為：

    Requirement 1-1:
    the cardinality of MIS-based IDS Game is X

    Requirement 1-2:
    the cardinality of Symmetric MDS-based IDS Game is Y

    Requirement 2:
    the cardinality of Matching Game is Z

其中 X, Y, Z 為三題 solver 回傳 cardinality。

---

## 4. Solver Design

以下內容以目前程式中 currently implemented 邏輯為準。

### 4.1 Problem 1: MIS-based IDS Game

#### State representation

- 二元向量 C = (c1, ..., cn)
- ci in {0, 1}
- 1 表示節點 i 為 active

#### Action / strategy

- 每位玩家 i 的策略是選 ci = 0 或 1
- 以非同步（asynchronous）方式逐步更新單一玩家策略

#### Utility function

- 先定義 Li = {j in Ni | deg(j) >= deg(i)}
- 效用：
  
  u_i(C) = c_i * (1 - alpha * sum_{j in L_i} c_j)
  
- 目前參數 alpha 固定為 2.0（符合 alpha > 1）

#### Best-response dynamics

- best response 規則（依目前實作）：
  - 若 Li 中存在 active 鄰居，BR_i = 0
  - 否則 BR_i = 1
- 每一步找出所有可改善玩家（目前策略不等於 BR）
- 從可改善玩家中隨機選一位更新
- 直到沒有人想偏離（converged）或超過步數上限

#### Tie-breaking / multi-start

- 多起點：全 0、全 1、以及多組隨機起點
- 同 cardinality 時以隨機方式打破平手
- 目前輸出邏輯：
  - 優先回傳 converged 且 IDS 合法的最小 cardinality
  - 若都不合法，回傳 fallback（並標記 is_valid=False）

---

### 4.2 Problem 2: Symmetric MDS-based IDS Game

#### State representation

- 同樣使用二元向量 C，ci in {0, 1}

#### Action / strategy

- 玩家 i 在 0/1 之間選擇
- 每回合比較 ci=0 與 ci=1 的效用後決定 BR

#### Utility function

- Mi = Ni union {i}
- v_i(C) = sum_{j in M_i} c_j
- g_i(C) = alpha if v_i(C)=1, else 0
- w_i(C) = sum_{j in N_i} c_i*c_j*gamma

- 效用：
  - 若 ci=1：
    
    u_i(C) = sum_{j in M_i} g_j(C) - beta - w_i(C)
  - 若 ci=0：u_i(C)=0

目前參數設定：

- alpha = 2.0
- beta = 1.0
- gamma = n*alpha + 1.0

且程式內有顯式檢查參數條件：

- alpha > 1
- 0 < beta < alpha
- gamma > n*alpha

#### Best-response dynamics

- 對每個 i 計算 BR_i（直接比較 action=0/1 效用）
- 同效用時目前採隨機 tie-break
- 每步從 improvable players 隨機挑一位更新
- 直到 converged 或達步數上限

#### Tie-breaking / multi-start

- 多起點策略與 Problem 1 類似（含隨機起點）
- 目標是找到 converged 且 IDS 合法解中的較小 cardinality
- 若未找到合法解，回傳 fallback 並保留狀態資訊供分析

---

### 4.3 Problem 3: Matching Game

#### State representation

- strategy_state 長度 n
- 每位玩家 i 的策略為：
  - None（不提案）
  - 或某個鄰居節點編號 j（提案給 j）

#### Action / strategy

- 玩家可在 None 與其鄰居集合中選擇
- 互相提案（i->j 且 j->i）才形成一條 matching edge
- matching cardinality 以 matched edge 數量計算（不是 matched vertices）

#### Utility function

對玩家 i：

- 選 None：0
- 選 j 且 j 也選 i（互配）：
  
  3 + bias(j)
- 選 j 且 j 選 None：
  
  1 + bias(j)
- 其他（j 選別人）：
  
  -1 + bias(j)

其中：

- bias(j) = 1 / (1 + degree(j))

#### Best-response dynamics

- 枚舉 i 的所有候選策略（None + neighbors(i)）
- 計算各策略效用，取最大者作 BR
- 更新順序 heuristic（目前已實作）：
  1. 先從可改善且目前未互配者中挑
  2. 再偏好較小 degree
  3. 最後隨機 tie-break

#### Tie-breaking / multi-start

- 多起點包含：
  - 全 None anchor
  - 混合型隨機起點
  - 偏 sparse（較多 None）
  - 偏 dense（較多提案）
- solver 目標：
  - 優先選合法且 maximal matching 的結果
  - 在合法 maximal 結果中取最大 cardinality
  - 若沒找到，回傳 fallback（可能非 maximal 或非合法）

#### 目前實作狀態備註

- matching validity 與 maximality 檢查在主程式與 checker 中都有 currently implemented 版本
- NE 檢查在 checker 端 currently implemented（以單人偏離枚舉驗證）

---

## 5. WS Generator

[314581030_HW1/src/ws_generator.py](314581030_HW1/src/ws_generator.py) 目前流程：

1. 參數檢查
2. 建立 ring lattice
3. 依機率 p 重連原始邊
4. 修補 isolated nodes（若有）
5. 輸出作業格式 bit-string

### 5.1 參數意義

- n: 節點數
- k: 每個節點在 ring 上連到左右各 k/2 個鄰居（需偶數，且 0 < k < n）
- p: rewiring 機率，範圍 [0,1]

### 5.2 no isolated node 條件

目前生成器有一個 repair 步驟：

- 若 rewiring 後某節點 degree=0，會額外補一條合法邊
- 目的是滿足 no isolated node 條件
- 這是保守修補：只加邊、不再刪邊

---

## 6. Checker / Verification

[314581030_HW1/src/checker.py](314581030_HW1/src/checker.py) 的角色是「外部驗證與批次 benchmark」，不是繳交用主入口。

### 6.1 前兩題 IDS 檢查

對 Problem 1/2，checker 會檢查：

- Independent: active 節點之間不得相鄰
- Dominating: 每個 inactive 節點至少有一個 active 鄰居

也有 NE 檢查（currently implemented）：

- Problem 1: 以 argmax best-response 集合檢查是否為 NE
- Problem 2: 以對應效用函數與參數做同樣 NE 檢查

### 6.2 第三題 Matching 檢查

對 Problem 3，checker 會檢查：

- strategy profile 是否 well-formed（None 或合法鄰居，且不能選自己）
- matching validity（互配形成邊、不得共用端點、邊需合法）
- maximality（是否仍存在可新增的未覆蓋邊）
- NE（枚舉單一玩家可偏離策略是否能嚴格提升效用）

以上項目目前在 checker 已有 currently implemented 檢查邏輯，不是 placeholder。

### 6.3 benchmark metrics 在看什麼

checker 會輸出每個 x 軸點（n 或 p）的平均/比例指標：

- avg_cardinality_problem1/2/3
- avg_move_count_problem1/2/3
- valid_rate_problem1/2/3
- maximal_rate_problem3
- ne_rate_problem1/2/3

並依模式畫圖：

- mode=n: cardinality vs n、move count vs n
- mode=p: cardinality vs p

---

## 7. How to Run

以下示範皆以專案根目錄為起點。

### 7.1 執行主程式

    cd 314581030_HW1/src
    python3 314581030_HW1_main.py 6 010000 101100 010010 010010 001101 000010

### 7.2 只生成 WS 測資（輸出為一行作業格式）

    cd 314581030_HW1/src
    python3 ws_generator.py --n 30 --k 4 --p 0.2 --seed 42

### 7.3 生成後直接跑主程式（--run-main）

    cd 314581030_HW1/src
    python3 ws_generator.py --n 30 --k 4 --p 0.2 --seed 42 --run-main

### 7.4 跑 checker：固定 p、掃 n

    cd 314581030_HW1/src
    python3 checker.py --mode n --n-values 20 40 60 --k 4 --p 0.2 --trials 5 --seed-base 42

### 7.5 跑 checker：固定 n、掃 p

    cd 314581030_HW1/src
    python3 checker.py --mode p --n 60 --k 4 --p-values 0.0 0.1 0.2 0.4 0.8 --trials 5 --seed-base 42

### 7.6 測試（minimum smoke test）

    cd 314581030_HW1/src
    python3 -m unittest test_minimum.py

### 7.7 套件需求備註

checker 會用到 matplotlib，若環境尚未安裝可先安裝：

    pip install matplotlib

---

## 8. Notes on AI Assistance

本專案開發過程有使用生成式 AI 進行以下協助（currently used）：

- 程式草稿與函式骨架整理
- 重構建議與命名一致化
- README/文件草稿撰寫與章節化
- 測試與驗證流程的整理建議

原始 prompts 與更細節的互動紀錄，預計另外整理，不放在此 README。

---

## Current Limitations / TODO（務實註記）

1. 主程式輸入驗證尚未強制檢查「是否無向圖、是否對角線為 0」；目前屬 TODO（需再對照作業最終規格）。
2. solver 目前以 heuristic multi-start + asynchronous best-response 為主，尚未提供理論最優解保證。
3. 測試檔目前只有 minimum smoke test；更完整的單元測試與壓力測試仍待補強。
4. checker 側重實驗驗證，不是作業繳交主流程；報告中需再精簡為課程要求格式。
