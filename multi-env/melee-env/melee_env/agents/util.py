import numpy as np
import melee
from melee.enums import Action
from collections import deque


class ObservationSpace:
    def __init__(self):
        self.previous_gamestate = None
        self.current_gamestate = None

    def set_player_keys(self, keys):
        self.player_keys = keys

    def get_stocks(self, gamestate):
        stocks = [gamestate.players[i].stock for i in list(
            gamestate.players.keys())]
        return np.array([stocks]).T  # players x 1

    def get_actions(self, gamestate):
        actions = [gamestate.players[i].action.value for i in list(
            gamestate.players.keys())]
        action_frames = [gamestate.players[i].action_frame for i in list(
            gamestate.players.keys())]
        hitstun_frames_left = [gamestate.players[i].hitstun_frames_left for i in list(
            gamestate.players.keys())]

        # players x 3
        return np.array([actions, action_frames, hitstun_frames_left]).T

    def get_positions(self, gamestate):
        x_positions = [gamestate.players[i].position.x for i in list(
            gamestate.players.keys())]
        y_positions = [gamestate.players[i].position.y for i in list(
            gamestate.players.keys())]

        return np.array([x_positions, y_positions]).T  # players x 2

    def __call__(self, gamestate):
        reward = (0, 0)
        info = None
        self.current_gamestate = gamestate

        if self.previous_gamestate is not None:
            p1_dmg = (
                self.current_gamestate.players[1].percent
                - self.previous_gamestate.players[1].percent
            )
            p1_shield_dmg = (
                self.previous_gamestate.players[1].shield_strength
                - self.current_gamestate.players[1].shield_strength
            ) / (self.current_gamestate.players[1].shield_strength + 1)
            p1_stock_loss = int(self.previous_gamestate.players[1].stock) - int(
                self.current_gamestate.players[1].stock
            )
            p2_dmg = (
                self.current_gamestate.players[2].percent
                - self.previous_gamestate.players[2].percent
            )
            p2_shield_dmg = (
                self.previous_gamestate.players[2].shield_strength
                - self.current_gamestate.players[2].shield_strength
            ) / (self.current_gamestate.players[2].shield_strength + 1)
            p2_stock_loss = int(self.previous_gamestate.players[2].stock) - int(
                self.current_gamestate.players[2].stock
            )

            p1_stock_loss *= abs(200 -
                                 self.current_gamestate.players[1].percent) / 200
            p2_stock_loss *= abs(200 -
                                 self.current_gamestate.players[2].percent) / 200

            p1_dmg = max(p1_dmg, 0)
            p2_dmg = max(p2_dmg, 0)
            if p1_stock_loss > 1:
                p1_stock_loss = 0
            if p2_stock_loss > 1:
                p2_stock_loss = 0
            p1_stock_loss = max(p1_stock_loss, 0)
            p2_stock_loss = max(p2_stock_loss, 0)
            p1_shield_dmg = max(p1_shield_dmg, 0)
            p2_shield_dmg = max(p2_shield_dmg, 0)

            w_dmg, w_shield, w_stock = 0.1, 0.3, 8
            p1_loss = (
                w_dmg * p1_dmg + w_shield * p1_shield_dmg + w_stock * p1_stock_loss
            )
            p2_loss = (
                w_dmg * p2_dmg + w_shield * p2_shield_dmg + w_stock * p2_stock_loss
            )

            reward = (p2_loss - p1_loss, p1_loss - p2_loss)
        else:
            reward = (0, 0)

        self.previous_gamestate = self.current_gamestate

        stocks = np.array(
            [gamestate.players[i].stock for i in list(
                gamestate.players.keys())]
        )
        done = not np.sum(stocks[np.argsort(stocks)][::-1][1:])

        return (
            gamestate,
            reward,
            done,
            info,
        )

    def reset(self):
        self.__init__()
        # print("observation space got reset!")


class ActionSpace:
    def __init__(self):
        mid = np.sqrt(2) / 2

        self.stick_space_reduced = np.array(
            [
                [0.0, 0.0],  # no op
                [0.0, 1.0],
                [mid, mid],
                [1.0, 0.0],
                [mid, -mid],
                [0.0, -1.0],
                [-mid, -mid],
                [-1.0, 0.0],
                [-mid, mid],
            ]
        )

        self.button_space_reduced = np.array([0.0, 1.0, 2.0, 3.0, 4.0])

        # Action space size is total number of possible actions. In this case,
        #    is is all possible main stick positions * all c-stick positions *
        #    all the buttons. A normal controller has ~51040 possible main stick
        #    positions. Each trigger has 255 positions. The c-stick can be
        #    reduced to ~5 positions. Finally, if all buttons can be pressed
        #    in any combination, that results in 32 combinations. Not including
        #    the dpad or start button, that is 51040 * 5 * 255 * 2 * 32 which
        #    is a staggering 4.165 billion possible control states.

        # Given this, it is reasonable to reduce this. In the above class, the
        #    main stick has been reduced to the 8 cardinal positions plus the
        #    center (no-op). Only A, B, Z, and R are used, as these correspond
        #    to major in-game functions (attack, special, grab, shield). Every
        #    action can theoretically be performed with just these buttons. A
        #    final "button" is added for no-op.
        #
        #    Action space = 9 * 5 = 45 possible actions.
        self.action_space = np.zeros(
            (self.stick_space_reduced.shape[0] *
             self.button_space_reduced.shape[0], 3)
        )

        for button in self.button_space_reduced:
            self.action_space[
                int(button) * 9: (int(button) + 1) * 9, :2
            ] = self.stick_space_reduced
            self.action_space[int(button) *
                              9: (int(button) + 1) * 9, 2] = button

        # self.action_space will look like this, where the first two columns
        #   represent the control stick's position, and the final column is the
        #   currently depressed button.

        # ACT  Left/Right    Up/Down      Button
        # ---  ------        ------       ------
        # 0   [ 0.        ,  0.        ,  0. (NO-OP)] Center  ---
        # 1   [ 0.        ,  1.        ,  0.        ] Up         |
        # 2   [ 0.70710678,  0.70710678,  0.        ] Up/Right   |
        # 3   [ 1.        ,  0.        ,  0.        ] Right      |
        # 4   [ 0.70710678, -0.70710678,  0.        ] Down/Right |- these repeat
        # 5   [ 0.        , -1.        ,  0.        ] Down       |
        # 6   [-0.70710678, -0.70710678,  0.        ] Down/Left  |
        # 7   [-1.        ,  0.        ,  0.        ] Left       |
        # 8   [-0.70710678,  0.70710678,  0.        ] Up/Left  ---
        # 9   [ 0.        ,  0.        ,  1. (A)    ]
        # 10  [ 0.        ,  1.        ,  1.        ]
        # 11  [ 0.70710678,  0.70710678,  1.        ]
        # 12  [ 1.        ,  0.        ,  1.        ]
        # 13  [ 0.70710678, -0.70710678,  1.        ]
        # 14  [ 0.        , -1.        ,  1.        ]
        # 15  [-0.70710678, -0.70710678,  1.        ]
        # 16  [-1.        ,  0.        ,  1.        ]
        # 17  [-0.70710678,  0.70710678,  1.        ]
        # 18  [ 0.        ,  0.        ,  2. (B)    ]
        # 19  [ 0.        ,  1.        ,  2.        ]
        # 20  [ 0.70710678,  0.70710678,  2.        ]
        # 21  [ 1.        ,  0.        ,  2.        ]
        # 22  [ 0.70710678, -0.70710678,  2.        ]
        # 23  [ 0.        , -1.        ,  2.        ]
        # 24  [-0.70710678, -0.70710678,  2.        ]
        # 25  [-1.        ,  0.        ,  2.        ]
        # 26  [-0.70710678,  0.70710678,  2.        ]
        # 27  [ 0.        ,  0.        ,  3. (Z)    ]
        # 28  [ 0.        ,  1.        ,  3.        ]
        # 29  [ 0.70710678,  0.70710678,  3.        ]
        # 30  [ 1.        ,  0.        ,  3.        ]
        # 31  [ 0.70710678, -0.70710678,  3.        ]
        # 32  [ 0.        , -1.        ,  3.        ]
        # 33  [-0.70710678, -0.70710678,  3.        ]
        # 34  [-1.        ,  0.        ,  3.        ]
        # 35  [-0.70710678,  0.70710678,  3.        ]
        # 36  [ 0.        ,  0.        ,  4. (R)    ]
        # 37  [ 0.        ,  1.        ,  4.        ]
        # 38  [ 0.70710678,  0.70710678,  4.        ]
        # 39  [ 1.        ,  0.        ,  4.        ]
        # 40  [ 0.70710678, -0.70710678,  4.        ]
        # 41  [ 0.        , -1.        ,  4.        ]
        # 42  [-0.70710678, -0.70710678,  4.        ]
        # 43  [-1.        ,  0.        ,  4.        ]
        # 45  [-0.70710678,  0.70710678,  4.        ]

        self.size = self.action_space.shape[0]

    def sample(self):
        return np.random.choice(self.size)

    def __call__(self, action):
        if action > self.size - 1:
            exit("Error: invalid action!")

        return ControlState(self.action_space[action])


class ControlState:
    def __init__(self, state):
        # state: [A, B, X, Y, Z, digital L, digital R, main x, main y, c stick x, c stick y, L, R]
        # range of state => idx 0~6: bool, 7~10: -1~1 float, 11~12: 0~1 float
        self.state = state
        self.buttons = [
            melee.enums.Button.BUTTON_A,
            melee.enums.Button.BUTTON_B,
            melee.enums.Button.BUTTON_X,
            melee.enums.Button.BUTTON_Y,
            melee.enums.Button.BUTTON_Z
        ]

    def __call__(self, controller):
        controller.release_all()
        for i in range(5):
            if self.state[i]:
                controller.press_button(self.buttons[i])
        controller.tilt_analog_unit(melee.enums.Button.BUTTON_MAIN,
                                    self.state[7], self.state[8])
        controller.tilt_analog_unit(melee.enums.Button.BUTTON_C,
                                self.state[9], self.state[10])
        if self.state[5]:
            controller.press_button(melee.Button.BUTTON_L)
        else:
            controller.press_shoulder(melee.enums.Button.BUTTON_L, self.state[11])
        
        if self.state[6]:
            controller.press_button(melee.Button.BUTTON_R)
        else:
            controller.press_shoulder(melee.enums.Button.BUTTON_R, self.state[12])


def from_observation_space(act):
    def get_observation(self, *args):
        gamestate = args[0]
        observation = self.observation_space(gamestate)
        return act(self, observation)

    return get_observation


def from_action_space(act):
    def get_action_encoding(self, *args):
        gamestate = args[0]
        action = act(self, gamestate)
        control = self.action_space(action)
        control(self.controller)
        return

    return get_action_encoding
