import os
import tqdm
import yaml
import time
import torch
import argparse
from melee import enums
from agent_loader import AgentLoader
from melee_env.env import MeleeEnv
from melee_env.agents.util import ObservationSpace

def get_config(path: str) -> dict:
    """
    Get config

    Args:
    - path: str, path to config file

    Returns:
    - config: dict, config
    """

    with open(path, "r", encoding="utf-8") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    return config


def get_character_enum(name: str) -> int:

    mapping = {
        "MARIO": enums.Character.MARIO,
        "FOX": enums.Character.FOX,
        "CPTFALCON": enums.Character.CPTFALCON,
        "DK": enums.Character.DK,
        "KIRBY": enums.Character.KIRBY,
        "BOWSER": enums.Character.BOWSER,
        "LINK": enums.Character.LINK,
        "SHEIK": enums.Character.SHEIK,
        "NESS": enums.Character.NESS,
        "PEACH": enums.Character.PEACH,
        "POPO": enums.Character.POPO,
        "NANA": enums.Character.NANA,
        "PIKACHU": enums.Character.PIKACHU,
        "SAMUS": enums.Character.SAMUS,
        "YOSHI": enums.Character.YOSHI,
        "JIGGLYPUFF": enums.Character.JIGGLYPUFF,
        "MEWTWO": enums.Character.MEWTWO,
        "LUIGI": enums.Character.LUIGI,
        "MARTH": enums.Character.MARTH,
        "ZELDA": enums.Character.ZELDA,
        "YLINK": enums.Character.YLINK,
        "DOC": enums.Character.DOC,
        "FALCO": enums.Character.FALCO,
        "PICHU": enums.Character.PICHU,
        "GAMEANDWATCH": enums.Character.GAMEANDWATCH,
        "GANONDORF": enums.Character.GANONDORF,
        "ROY": enums.Character.ROY,
        "WIREFRAME_MALE": enums.Character.WIREFRAME_MALE,
        "WIREFRAME_FEMALE": enums.Character.WIREFRAME_FEMALE,
        "GIGA_BOWSER": enums.Character.GIGA_BOWSER,
        "SANDBAG": enums.Character.SANDBAG,
    }

    return mapping[name]


def get_stage_enum(name: str) -> int:

    mapping = {
        "FINAL_DESTINATION": enums.Stage.FINAL_DESTINATION,
        "BATTLEFIELD": enums.Stage.BATTLEFIELD,
        "POKEMON_STADIUM": enums.Stage.POKEMON_STADIUM,
        "DREAMLAND": enums.Stage.DREAMLAND,
        "FOUNTAIN_OF_DREAMS": enums.Stage.FOUNTAIN_OF_DREAMS,
        "YOSHIS_STORY": enums.Stage.YOSHIS_STORY,
        "RANDOM_STAGE": enums.Stage.RANDOM_STAGE,
    }

    return mapping[name]


def main(_config):
    
    buffer_cnt = 0
    done_result = None
    observation_space = ObservationSpace()
    print("[Log] loading agents... ")
    p1_agent = AgentLoader(
        player_id=1, 
        device=torch.device("cuda:0"), 
        character=get_character_enum(_config["p1_character"]), 
        stage=get_stage_enum(_config["stage"]), 
        config_path=_config["p1_agent_config_path"]
    )()
    print("[Log] player 1 agent loaded successfully")
    p2_agent = AgentLoader(
        player_id=2, 
        device=torch.device("cuda:1"), 
        character=get_character_enum(_config["p2_character"]), 
        stage=get_stage_enum(_config["stage"]), 
        config_path=_config["p2_agent_config_path"]
    )()
    print("[Log] player 2 agent loaded successfully")
    
    players = [p1_agent, p2_agent]
    
    print("[Log] Initializing environment... ")
    env = MeleeEnv(
        iso_path=_config["iso_path"],
        players=players,
        fast_forward=_config["fast_forward"],
        blocking_input=_config["blocking_input"],
        save_replays=_config["save_replays"],
        port=_config["port"]
    )
    print("[Log] Environment initialized successfully")
    
    print("[Log] Starting environment... ")
    env.start()
    print("[Log] Environment started successfully")
    
    print("[Log] Resetting environment... ")
    now_s, _ = env.reset(_config["stage"])
    print("[Log] Environment reset successfully")
    
    pbar = tqdm.trange(1)
    
    for step_cnt in range(_config["max_steps"]):
        # Menu selecting phase
        if step_cnt <= 100:
            action_pair = [0, 0]
            now_s = env.step(*action_pair)
            continue
        
        # Act of p1
        p1_act_start_time = time.time()
        p1_action = players[0].act(now_s)
        p1_act_end_time = time.time()
        p1_act_time = p1_act_end_time - p1_act_start_time
        
        if p1_act_time > _config["max_act_time"]:
            print(f"[Log] Player 1's action time exceeded the limit: {p1_act_time}, no action will be applied")
            p1_action = 0
            
        # Act of p2
        p2_act_start_time = time.time()
        p2_action = players[1].act(now_s)
        p2_act_end_time = time.time()
        p2_act_time = p2_act_end_time - p2_act_start_time
        
        if p2_act_time > _config["max_act_time"]:
            print(f"[Log] Player 2's action time exceeded the limit: {p2_act_time}, no action will be applied")
            p2_action = 0
            
        action_pair = [p1_action, p2_action]
        
        now_s, _, done, _ = observation_space(env.step(*action_pair))

        pbar.update(1)
        pbar.set_postfix(
            {
                "Player 1's action": p1_action, 
                "Player 2's action": p2_action,
                "player 1's stock": now_s.players[1].stock,
                "player 2's stock": now_s.players[2].stock,
                "player 1's percent": now_s.players[1].percent,
                "player 2's percent": now_s.players[2].percent
            }
        )
        
        # Check if the game is done
        if done:
            buffer_cnt += 1
            done_result = now_s
        
        # Break if buffer is full, for the replay doesn't end too early    
        if buffer_cnt >= 500:
            break
    
    # If the game is not done and ended by the max_steps, set done_result to the last state
    if done_result is None:
        print("[Log] Game ended by the max_steps")
        done_result = now_s
    else:
        print("[Log] Game ended by the game rule")

    # Determine winner
    if done_result.players[1].stock < done_result.players[2].stock:
        print(f"[Log] Player 1 wins, stock difference, player 1's stock: {done_result.players[1].stock}, player 2's stock: {done_result.players[2].stock}")
    
    elif done_result.players[1].stock > done_result.players[2].stock:
        print(f"[Log] Player 2 wins, stock difference, player 1's stock: {done_result.players[1].stock}, player 2's stock: {done_result.players[2].stock}")
    
    else:
        if done_result.players[1].percent < done_result.players[2].percent:
            print(f"[Log] Player 1 wins, percent difference, player 1's stock: {done_result.players[1].stock}, player 2's stock: {done_result.players[2].stock}, player 1's percent: {done_result.players[1].percent}, player 2's percent: {done_result.players[2].percent}")
    
        elif done_result.players[1].percent > done_result.players[2].percent:
            print(f"[Log] Player 2 wins, percent difference, player 1's stock: {done_result.players[1].stock}, player 2's stock: {done_result.players[2].stock}, player 1's percent: {done_result.players[1].percent}, player 2's percent: {done_result.players[2].percent}")
    
        else:
            print(f"[Log] Draw, player 1's stock: {done_result.players[1].stock}, player 2's stock: {done_result.players[2].stock}, player 1's percent: {done_result.players[1].percent}, player 2's percent: {done_result.players[2].percent}")
    
    print("[Log] Closing environment... ")
    env.close()
    print("[Log] Environment closed successfully")
    
    print("[Log] Matchmaking finished")
    
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the matchmaker")
    parser.add_argument(
         "--config_path",
        type=str,
        default="./match_maker_config.yaml",
        help="Path to config file"
    )
    args = parser.parse_args()
    
    _config = get_config(args.config_path)
    
    main(_config)