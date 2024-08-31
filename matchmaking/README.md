Agent format
============

To make the agent run on matchmaking.py, three conditions should be satisfied.
### 1. Agent must inherit **melee_env.basics.Agent** class.
example) 
```python
from melee_env.agents.basic import Agent


class ExampleAgent(Agent):
    def __init__(self, ...):
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
from melee_env.agents.util import ActionSpace


class ExampleAgent(Agent):
    def __init__(self, ...):
        # You can use custom action space too.
        self.action_space = ActionSpace()
        ...
    
    def act(self, state: GameState) -> int:
        ... 
        return action
```

### 4. Agent must have player_id, device, character, stage, and config arguments in \_\_init\_\_ method.

\_\_init\_\_ method should only take 5 arguments. 

example)
```python
from melee.gamestate import GameState
from melee.enums import Character, Stage
from melee_env.agents.basic import Agent
from melee_env.agents.util import ActionSpace


class ExampleAgent(Agent):
    def __init__(self, player_id: int, device: torch.device, character: Character, stage: Stage, config: dict):
        self.player_id = player_id  # Actually, this is not necessary information.
        self.character = character  # Agent's Character
        self.stage = stage  # Current Stage
        self.device = device  # Device for GPU Allocation
        self.config = config  # Miscellaneous arguments for initializing the agent
        # You can use custom action space too.
        self.action_space = ActionSpace()
        ...
    
    def act(self, state: GameState) -> int:
        ... 
        return action
```

About AgentLoader
=================
AgentLoader will load your agent instance with initialization.  
You have to fill up the config yaml file to load the agent.


About Matchmaker
================