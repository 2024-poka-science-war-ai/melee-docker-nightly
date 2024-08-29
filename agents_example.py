import argparse
import tqdm
from melee import enums
from melee_env.agents.basic import *
from melee_env.env import MeleeEnv

parser = argparse.ArgumentParser(
    description="Example melee-env demonstration.")
parser.add_argument(
    "--iso", default="ssbm.iso", type=str, help="Path to your NTSC 1.02/PAL SSBM Melee ISO"
)

args = parser.parse_args()

players = [Rest(), Rest()]
try:
    env = MeleeEnv(args.iso, players, fast_forward=True)
    episodes = 1
    reward = 0
    print("start env")
    env.start()

    pbar = tqdm.trange(1)

    for episode in range(episodes):
        gamestate, done = env.reset(enums.Stage.BATTLEFIELD)
        i = 0
        while not done and i < 1000:
            i += 1
            gamestate, r, done, _ = env.step(0, 0)
            pbar.update(1)
    env.close()

except:
    print("no Dolphin.ini, Copy one in to data files")
