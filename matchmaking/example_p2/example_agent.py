import torch
import random
import numpy as np
from melee.gamestate import GameState
from melee.enums import Character, Stage
from melee_env.agents.basic import Agent
from melee_env.agents.util import ActionSpace, ControlState


class ExampleActionSpace():
    def __init__(self):
        self.actions = np.array(
            [
                [False, False, False, False, False, False, False, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [False, False, False, False, False, False, False, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [False, False, False, False, False, False, False, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [False, False, False, False, False, False, False, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            ]
        )
        
        self.size = self.actions.shape[0]
        
    def sample(self):
        return np.random.choice(self.size)
    
    def __call__(self, action):
        assert 0 <= action < self.size, "Invalid action"
        return ControlState(self.actions[action])


class ExampleAgent(Agent):
    def __init__(self, player_id: int, device: torch.device, character: Character, stage: Stage, config: dict):
        super().__init__()
        self.player_id = player_id  # Actually, this is not necessary information.
        self.character = character  # Agent's Character
        self.stage = stage  # Current Stage
        self.device = device  # Device for GPU Allocation
        self.config = config  # Miscellaneous arguments for initializing the agent
        # You can use custom action space too.
        self.action_space = ExampleActionSpace()
        
    
    def act(self, state: GameState) -> int:
        return random.randint(0, 3)