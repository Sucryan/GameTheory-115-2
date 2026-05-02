from BaseAgent import BaseAgent

from collections import deque
import os
import random

import numpy as np

try:
    from stable_baselines3 import DQN

    SB3_AVAILABLE = True
    SB3_IMPORT_ERROR = None
except Exception as exc:
    DQN = None
    SB3_AVAILABLE = False
    SB3_IMPORT_ERROR = exc

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    TORCH_AVAILABLE = True
    TORCH_IMPORT_ERROR = None
except Exception as exc:
    torch = None
    nn = None
    F = None
    TORCH_AVAILABLE = False
    TORCH_IMPORT_ERROR = exc


if TORCH_AVAILABLE:
    class _TinyQNetwork(nn.Module):
        def __init__(self, obs_dim, action_dim):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(obs_dim, 64),
                nn.ReLU(),
                nn.Linear(64, 64),
                nn.ReLU(),
                nn.Linear(64, action_dim),
            )

        def forward(self, obs):
            return self.net(obs)
else:
    class _TinyQNetwork:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("PyTorch is required for the fallback DQN backend.")


class RLAgent(BaseAgent):
    def __init__(
        self,
        env,
        total_episodes=300,
        learning_rate=1e-3,
        buffer_size=10000,
        learning_starts=100,
        batch_size=64,
        gamma=0.95,
        gradient_steps=1,
        target_update_interval=250,
        exploration_fraction=0.3,
        exploration_initial_eps=1.0,
        exploration_final_eps=0.05,
        seed=None,
        device="auto",
        use_sb3=False,
    ):
        super().__init__(env, total_episodes)
        self.max_steps = getattr(env, "max_steps", 100)
        self.total_timesteps = max(1, total_episodes * self.max_steps)
        self.learning_rate = learning_rate
        self.buffer_size = buffer_size
        self.learning_starts = learning_starts
        self.batch_size = batch_size
        self.gamma = gamma
        self.gradient_steps = gradient_steps
        self.target_update_interval = target_update_interval
        self.exploration_fraction = exploration_fraction
        self.exploration_initial_eps = exploration_initial_eps
        self.exploration_final_eps = exploration_final_eps
        self.seed = seed
        self.device = device

        if use_sb3:
            if not SB3_AVAILABLE:
                raise RuntimeError(
                    "stable_baselines3 was requested but is not available. "
                    f"SB3 import error: {SB3_IMPORT_ERROR}"
                )
            self.backend = "sb3"
            self._init_sb3_model()
        else:
            self.backend = "torch"
            self._init_torch_model()

    def _init_sb3_model(self):
        self.model = DQN(
            "MlpPolicy",
            self.env,
            learning_rate=self.learning_rate,
            buffer_size=self.buffer_size,
            learning_starts=self.learning_starts,
            batch_size=self.batch_size,
            gamma=self.gamma,
            train_freq=1,
            gradient_steps=self.gradient_steps,
            target_update_interval=self.target_update_interval,
            exploration_fraction=self.exploration_fraction,
            exploration_initial_eps=self.exploration_initial_eps,
            exploration_final_eps=self.exploration_final_eps,
            policy_kwargs={"net_arch": [64, 64]},
            verbose=0,
            seed=self.seed,
            device=self.device,
        )
        self.model._total_timesteps = self.total_timesteps
        self.model.exploration_rate = self.exploration_initial_eps

    def learn(self, total_timesteps=None, **kwargs):
        if self.backend != "sb3":
            raise RuntimeError(
                "learn() is only for the optional SB3 backend. "
                "The default torch backend learns through update()."
            )

        timesteps = self.total_timesteps if total_timesteps is None else int(total_timesteps)
        kwargs.setdefault("reset_num_timesteps", False)
        return self.model.learn(total_timesteps=timesteps, **kwargs)

    def _init_torch_model(self):
        if not TORCH_AVAILABLE:
            raise RuntimeError(
                "RLAgent needs stable_baselines3 for the SB3 DQN backend, "
                "or torch for the fallback DQN backend. "
                f"SB3 import error: {SB3_IMPORT_ERROR}; "
                f"torch import error: {TORCH_IMPORT_ERROR}"
            )

        if self.seed is not None:
            random.seed(self.seed)
            np.random.seed(self.seed)
            torch.manual_seed(self.seed)

        if self.device == "auto":
            self.torch_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.torch_device = torch.device(self.device)

        obs_dim = int(np.prod(self.env.observation_space.shape))
        action_dim = int(self.env.action_space.n)
        self.q_net = _TinyQNetwork(obs_dim, action_dim).to(self.torch_device)
        self.target_q_net = _TinyQNetwork(obs_dim, action_dim).to(self.torch_device)
        self.target_q_net.load_state_dict(self.q_net.state_dict())
        self.optimizer = torch.optim.Adam(self.q_net.parameters(), lr=self.learning_rate)
        self.replay_buffer = deque(maxlen=self.buffer_size)
        self.num_timesteps = 0
        self.epsilon = self.exploration_initial_eps

    def act(self, state, explore):
        if self.backend == "sb3":
            action, _ = self.model.predict(state, deterministic=not explore)
            return int(np.asarray(action).item())

        if explore and np.random.rand() < self.epsilon:
            return int(self.action_space.sample())

        obs = self._obs_to_tensor(state)
        with torch.no_grad():
            q_values = self.q_net(obs)
        return int(torch.argmax(q_values, dim=1).item())

    def update(self, obs, action, reward, next_obs, done):
        if self.backend == "sb3":
            self._update_sb3(obs, action, reward, next_obs, done)
        else:
            self._update_torch(obs, action, reward, next_obs, done)

    def _update_sb3(self, obs, action, reward, next_obs, done):
        raise RuntimeError(
            "The optional SB3 backend uses the public model.learn() API and "
            "cannot be updated from externally supplied one-step transitions "
            "without making SB3 step the environment again. Use the default "
            "torch backend with main.py, or call learn() in a separate SB3 "
            "training flow."
        )

    def _update_torch(self, obs, action, reward, next_obs, done):
        self.replay_buffer.append(
            (
                np.asarray(obs, dtype=np.float32),
                int(action),
                float(reward),
                np.asarray(next_obs, dtype=np.float32),
                bool(done),
            )
        )

        self.num_timesteps += 1
        self._update_epsilon()

        if self.num_timesteps <= self.learning_starts:
            return
        if len(self.replay_buffer) < self.batch_size:
            return

        for _ in range(self.gradient_steps):
            self._train_torch_step()

        if self.num_timesteps % self.target_update_interval == 0:
            self.target_q_net.load_state_dict(self.q_net.state_dict())

    def _train_torch_step(self):
        batch = random.sample(self.replay_buffer, self.batch_size)
        obs, actions, rewards, next_obs, dones = zip(*batch)

        obs_tensor = torch.as_tensor(np.array(obs), dtype=torch.float32, device=self.torch_device)
        action_tensor = torch.as_tensor(actions, dtype=torch.long, device=self.torch_device).unsqueeze(1)
        reward_tensor = torch.as_tensor(rewards, dtype=torch.float32, device=self.torch_device)
        next_obs_tensor = torch.as_tensor(np.array(next_obs), dtype=torch.float32, device=self.torch_device)
        done_tensor = torch.as_tensor(dones, dtype=torch.float32, device=self.torch_device)

        current_q = self.q_net(obs_tensor).gather(1, action_tensor).squeeze(1)
        with torch.no_grad():
            next_q = self.target_q_net(next_obs_tensor).max(dim=1).values
            target_q = reward_tensor + (1.0 - done_tensor) * self.gamma * next_q

        loss = F.smooth_l1_loss(current_q, target_q)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

    def _update_epsilon(self):
        exploration_steps = max(1, int(self.exploration_fraction * self.total_timesteps))
        progress = min(1.0, self.num_timesteps / exploration_steps)
        self.epsilon = self.exploration_initial_eps + progress * (
            self.exploration_final_eps - self.exploration_initial_eps
        )

    def _obs_to_tensor(self, obs):
        obs_arr = np.asarray(obs, dtype=np.float32).reshape(1, -1)
        return torch.as_tensor(obs_arr, dtype=torch.float32, device=self.torch_device)

    def save_model(self, name="rl_agent_dqn"):
        if self.backend == "sb3":
            path = name if str(name).endswith(".zip") else f"{name}.zip"
            self.model.save(path)
        else:
            path = name if str(name).endswith((".pt", ".pth")) else f"{name}.pt"
            torch.save(
                {
                    "q_net": self.q_net.state_dict(),
                    "target_q_net": self.target_q_net.state_dict(),
                    "optimizer": self.optimizer.state_dict(),
                    "num_timesteps": self.num_timesteps,
                    "epsilon": self.epsilon,
                },
                path,
            )
        print("Training completed. Writing model to " + str(path))

    def load_model(self, name="rl_agent_dqn"):
        if self.backend == "sb3":
            path = self._resolve_model_path(name, ".zip")
            self.model = DQN.load(path, env=self.env, device=self.device)
            self.model._total_timesteps = self.total_timesteps
        else:
            path = self._resolve_model_path(name, ".pt")
            checkpoint = torch.load(path, map_location=self.torch_device)
            self.q_net.load_state_dict(checkpoint["q_net"])
            self.target_q_net.load_state_dict(checkpoint["target_q_net"])
            self.optimizer.load_state_dict(checkpoint["optimizer"])
            self.num_timesteps = checkpoint.get("num_timesteps", 0)
            self.epsilon = checkpoint.get("epsilon", self.exploration_final_eps)
        print("Reading model from " + str(path))

    def _resolve_model_path(self, name, suffix):
        path = str(name)
        if os.path.exists(path):
            return path
        if not path.endswith(suffix) and os.path.exists(path + suffix):
            return path + suffix
        return path if path.endswith(suffix) else path + suffix


DQNAgent = RLAgent
