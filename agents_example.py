import argparse
import tqdm
from melee import enums
from melee_env.agents.basic import *
from melee_env.env import MeleeEnv

parser = argparse.ArgumentParser(description="Example melee-env demonstration.")
parser.add_argument(
    "--iso", default="ssbm.iso", type=str, help="Path to your NTSC 1.02/PAL SSBM Melee ISO"
)

args = parser.parse_args()

players = [Rest(), NOOP(enums.Character.FOX)]

try:
    env = MeleeEnv(args.iso, players, fast_forward=True)
    episodes = 1
    reward = 0
    print("start env")
    env.start()

    pbar = tqdm.trange(1)

    for episode in range(episodes):
        gamestate, done = env.setup(enums.Stage.BATTLEFIELD)
        while not done:
            for i in range(len(players)):
                players[i].act(gamestate)
            gamestate, done = env.step()
            pbar.update(1)
    env.close()

except:
    print("no Dolphin.ini, Copy one in to data files")
