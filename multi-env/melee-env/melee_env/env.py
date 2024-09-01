import socket
import sys
import time

import melee
import numpy as np
from melee import enums
from melee_env.agents.util import ObservationSpace
from melee_env.dconfig import DolphinConfig
import psutil


def find_available_udp_port(start_port: int = 1024, end_port: int = 65535) -> int:
    for port in range(start_port, end_port + 1):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind(("", port))
                return port
        except OSError:
            continue
    raise OSError("no availiable port")


def kill_zombies(runtime_to_kill: float = 1200):
    """
    kill any dolphin emulators that have been running for more than 20 minutes
    """
    for proc in psutil.process_iter():
        try:
            if "dolphin-emu" in proc.name() and time.time() - proc.create_time() > runtime_to_kill:
                proc.kill()

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            print(f"zombie process kill failure, pid={proc.pid}")


class MeleeEnv:
    def __init__(
        self,
        iso_path,
        players,
        fast_forward=False,
        blocking_input=True,
        ai_starts_game=True,
        save_replays=False,
        port=None,
        save_action=False,
    ):
        self.d = DolphinConfig()
        self.d.set_ff(fast_forward)

        self.iso_path = iso_path
        self.players = players
        self.controllers = []

        # inform other players of other players
        # for player in self.players:
        #     player.set_player_keys(len(self.players))

        # if len(self.players) == 2:
        #     self.d.set_center_p2_hud(True)
        # else:
        #     self.d.set_center_p2_hud(False)

        self.blocking_input = blocking_input
        self.ai_starts_game = ai_starts_game
        self.observation_space = ObservationSpace()

        self.gamestate = None
        self.console = None
        self.menu_control_agent = 0
        self.ai_press_start = ai_starts_game
        self.save_replays = save_replays
        self.port = port
        self.save_action = save_action
        self.action_history = {0: [], 1: []}

    def start(self):
        if sys.platform == "linux":
            dolphin_home_path = str(self.d.slippi_home) + "/"
        elif sys.platform == "win32":
            dolphin_home_path = None

        self.console = melee.Console(
            path=str(self.d.slippi_bin_path),
            dolphin_home_path=dolphin_home_path,
            blocking_input=self.blocking_input,
            tmp_home_directory=True,
            slippi_port=find_available_udp_port() if self.port is None else self.port,
            gfx_backend="Null",
            setup_gecko_codes=True,
            disable_audio=True,
            save_replays=self.save_replays
        )

        # print(self.console.dolphin_home_path)  # add to logging later
        # Configure Dolphin for the correct controller setup, add controllers
        human_detected = False

        for i in range(len(self.players)):
            curr_player = self.players[i]
            if curr_player.agent_type == "HMN":
                self.d.set_controller_type(
                    i + 1, enums.ControllerType.GCN_ADAPTER)
                curr_player.controller = melee.Controller(
                    console=self.console,
                    port=i + 1,
                    type=melee.ControllerType.GCN_ADAPTER,
                )
                curr_player.port = i + 1
                human_detected = True
            elif curr_player.agent_type in ["AI", "CPU"]:
                self.d.set_controller_type(
                    i + 1, enums.ControllerType.GCN_ADAPTER)
                curr_player.controller = melee.Controller(
                    console=self.console, port=i + 1
                )
                self.menu_control_agent = i
                curr_player.port = i + 1
            else:  # no player
                self.d.set_controller_type(
                    i + 1, enums.ControllerType.UNPLUGGED)

            self.controllers.append(curr_player.controller)
        if self.ai_starts_game and not human_detected:
            self.ai_press_start = True

        else:
            self.ai_press_start = (
                # don't let ai press start without the human player joining in.
                False
            )

        if self.ai_starts_game and self.ai_press_start:
            self.players[self.menu_control_agent].press_start = True

        self.console.run(iso_path=self.iso_path)
        self.console.connect()

        [player.controller.connect()
         for player in self.players if player is not None]

        self.gamestate = self.console.step()

    def reset(self, stage):
        self.observation_space.reset()
        for player in self.players:
            player.defeated = False

        while True:
            self.gamestate = self.console.step()
            if self.gamestate.menu_state is melee.Menu.CHARACTER_SELECT:
                for i in range(len(self.players)):
                    if self.players[i].agent_type == "AI":
                        melee.MenuHelper.choose_character(
                            character=self.players[i].character,
                            gamestate=self.gamestate,
                            controller=self.players[i].controller,
                            costume=i,
                            swag=False,
                            start=self.players[i].press_start,
                        )
                    if self.players[i].agent_type == "CPU":
                        melee.MenuHelper.choose_character(
                            character=self.players[i].character,
                            gamestate=self.gamestate,
                            controller=self.players[i].controller,
                            costume=i,
                            swag=False,
                            cpu_level=self.players[i].lvl,
                            start=self.players[i].press_start,
                        )

            elif self.gamestate.menu_state is melee.Menu.STAGE_SELECT:
                # time.sleep(0.1)
                melee.MenuHelper.choose_stage(
                    stage=stage,
                    gamestate=self.gamestate,
                    controller=self.players[self.menu_control_agent].controller,
                )

            elif self.gamestate.menu_state in [
                melee.Menu.IN_GAME,
                melee.Menu.SUDDEN_DEATH,
            ]:
                return self.gamestate, False  # game is not done on start

            else:
                melee.MenuHelper.choose_versus_mode(
                    self.gamestate, self.players[self.menu_control_agent].controller
                )

    def step(self, *actions):
        for i, player in enumerate(self.players):
            if player.agent_type == "CPU":
                continue
            action = actions[i]
            control = player.action_space(action)
            if self.save_action:
                self.action_history[i].append((control.state))
            control(player.controller)

        if self.gamestate.menu_state in [melee.Menu.IN_GAME, melee.Menu.SUDDEN_DEATH]:
            self.gamestate = self.console.step()
        return self.gamestate

    def close(self):
        for c in self.controllers:
            c.disconnect()

        self.observation_space.reset()
        self.gamestate = None
        self.console.stop()
        
        if self.save_action:
            import pickle
            with open("action_history.pkl", "wb") as f:
                pickle.dump(self.action_history, f)
            print("[Env] Action history saved")