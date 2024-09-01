Agent format
============

To make the agent run on matchmaking.py, three conditions should be satisfied.
### 1. Agent must inherit **melee_env.basics.Agent** class.
example) 
```python
from melee_env.agents.basic import Agent


class ExampleAgent(Agent):
    def __init__(self, ...):
        super().__init__()
        ...
    
    ...
```

### 2. Agent must have **.act(self, state)** method
example)
```python
from melee.gamestate import GameState
from melee_env.agents.basic import Agent


class ExampleAgent(Agent):
    def __init__(self, ...):
        super().__init__()
        ...
    
    def act(self, state: GameState) -> int:
        ... 
        return action
```

### 3. Agent must have **action_space** attribute

example)
```python
from melee.gamestate import GameState
from melee_env.agents.basic import Agent
from melee_env.agents.util import ControlState

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
    
    def __call__(self, action) -> ControlState:
        assert 0 <= action < self.size, "Invalid action"
        return ControlState(self.actions[action])


class ExampleAgent(Agent):
    def __init__(self, ...):
        super().__init__()
        # You can use custom action space too.
        self.action_space = ExampleActionSpace()
    
    def act(self, state: GameState) -> int:
        ...
        return action
```
Also, Action space must have \_\_call\_\_(self, action): 


### 4. Agent must have player_id, device, character, stage, and config arguments in \_\_init\_\_ method.

\_\_init\_\_ method should only take 5 arguments. 

example)
```python
import torch
import random
import numpy as np
from melee.gamestate import GameState
from melee.enums import Character, Stage
from melee_env.agents.basic import Agent
from melee_env.agents.util import ControlState


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
        ...
        return action
```

About Matchmaker
================
Example Content of match_macker_config.yaml  
(Every path should be absolute path)
```yaml
p1_character: FOX  # MARIO, LUIGI, YOSHI, DOC, LINK, PIKACHU
p1_agent_config_path: "/root/matchmaking/example_p1/example_agent_config.yaml"

p2_character: FOX
p2_agent_config_path: "/root/matchmaking/example_p2/example_agent_config.yaml"

stage: FINAL_DESTINATION  # FINAL_DESTINATION, BATTLEFIELD, POKEMON_STADIUM

max_act_time: 0.01  # Maximum time for an agent to act, actions will be ignored if time exceeds this value

# Misc env settings
iso_path: "/root/ssbm.iso"  # Path to the Melee ISO
fast_forward: False  # Fast forward the game to the first frame where both agents have sent their inputs
blocking_input: True  # one frame will pass when all agents have sent their inputs
save_replays: True  # Save replays to record the match, saving location: /root/slippi_replays
port: 51441  # Default port for Slippi
max_steps: 28800  # Sufficiently big number
```

Type below instruction to run the matchmaker.py

```bash
python3 matchmaker.py
```

it will show the env state, win or lose, current stock and damage percents of AI agents.

About AgentLoader
=================
AgentLoader will load your agent instance with initialization.  
You have to fill up the config yaml file to load the agent.  
AgentLoader will load the agent using agent config yaml
In the example case, the agent config yaml files are 
/example_p1/example_agent_config.yaml and /example_p2/example_agent_config.yaml.  
Example Content of example_agent_config.yaml  
(Every path should be absolute path)

```yaml
agent_module_dir: "/root/matchmaking/example_p1"
agent_module_name: "example_agent"
agent_class_name: "ExampleAgent"
```
agent_module_dir, agent_module_name, agent_class_name is a necessary option to load the agent to matchmaker.py.  
You can add additional options to initialize your agents.
