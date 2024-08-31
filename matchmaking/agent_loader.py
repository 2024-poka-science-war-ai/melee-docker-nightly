import os
import sys
import yaml
import importlib


class AgentLoader:
    
    def __init__(self, player_id, device, character, stage, config_path):
        """
        Initialize AgentLoader
        :param player_id: int, player id, 1 or 2
        :param device: torch.device, device, cuda:0 or cuda:1
        :param character: melee.enums.Character, character
        :param stage: melee.enums.Stage, stage
        :param config_path: str, path to config file
        """
        
        self.player_id = player_id
        self.device = device
        self.character = character
        self.stage = stage
        self.have_loaded_config = True
        self.config = None
        self.agent = None
        self.load_config(config_path)
    
    def load_config(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                config = yaml.load(f, Loader=yaml.FullLoader)
            self.config = config
            self.have_loaded_config = True
        except:
            raise Exception(f"Failed to load config file of player {self.player_id}")        
        
        return config
    
    def __call__(self):
        assert self.have_loaded_config, "Config file not loaded, player {self.player_id}"

        sys.path.append(self.config["agent_module_dir"])
        module_name = self.config["agent_module_name"]
        class_name = self.config["agent_class_name"]
        
        module = importlib.import_module(module_name)
        agent = getattr(module, class_name)(
            player_id=self.player_id, 
            device=self.device, 
            character=self.character, 
            stage=self.stage, 
            config=self.config
        )
        
        self.agent = agent
        
        return self.agent
