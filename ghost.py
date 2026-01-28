import random

import arcade

import constants
from constants import RIGHT, LEFT, UP, DOWN, HOLD, WINDOW_HEIGHT, WINDOW_WIDTH

ghost_mex_speed = 3.33
random_interval = 250

ghost_image = [
    [
        arcade.load_texture("images/BlinkyUp.png"),
        arcade.load_texture("images/BlinkyLeft.png"),
        arcade.load_texture("images/BlinkyRight.png"),
        arcade.load_texture("images/BlinkyUp.png"),
        arcade.load_texture("images/BlinkyDown.png"),
    ],
    [
        arcade.load_texture("images/PinkyUp.png"),
        arcade.load_texture("images/PinkyLeft.png"),
        arcade.load_texture("images/PinkyRight.png"),
        arcade.load_texture("images/PinkyUp.png"),
        arcade.load_texture("images/PinkyDown.png"),
    ],
    [
        arcade.load_texture("images/InkyUp.png"),
        arcade.load_texture("images/InkyLeft.png"),
        arcade.load_texture("images/InkyRight.png"),
        arcade.load_texture("images/InkyUp.png"),
        arcade.load_texture("images/InkyDown.png"),
    ],
    [
        arcade.load_texture("images/ClydeUp.png"),
        arcade.load_texture("images/ClydeLeft.png"),
        arcade.load_texture("images/ClydeRight.png"),
        arcade.load_texture("images/ClydeUp.png"),
        arcade.load_texture("images/ClydeDown.png"),
    ],
]

frightened = arcade.load_texture("images/frightened.png")
frightenedW = arcade.load_texture("images/frightened2.png")
caught = arcade.load_texture("images/caught.png")

caught_sound = arcade.load_sound("sounds/eatghost.wav")
ghost_score = [200, 400, 800, 1600]
delay_to_release = [1, 10, 30, 90]
delay_to_release_after_caught = [1, 5, 15, 25]

cycle_order = [
    [RIGHT, DOWN, LEFT, UP],
    [LEFT, DOWN, RIGHT, UP],
    [RIGHT, UP, LEFT, DOWN],
    [LEFT, UP, RIGHT, DOWN],
    [DOWN, RIGHT, UP, LEFT],
    [DOWN, LEFT, UP, RIGHT],
    [UP, RIGHT, DOWN, LEFT],
    [UP, LEFT, DOWN, RIGHT],
]


class Ghost(arcade.Sprite):
    fright_timer = 0
    ghost_exit_point = ()

    BLINKY = 0
    PINKY = 1
    INKY = 2
    CLYDE = 3

    CHASE = 0
    SCATTER = 1
    FRIGHTENED = 2
    RANDOM = 3
    CAUGHT = 4

    def __init__(self, gtype, x, y):
        self.gtype = gtype
        x = x * 20 + 20
        y = WINDOW_HEIGHT - (y * 20 + 40)
        if gtype == Ghost.BLINKY:
            x -= 10
            Ghost.ghost_exit_point = (x, y)
        super().__init__(frightened, 18 / 20, x, y)
        self.start_position = (x, y)
        self.speed = ghost_mex_speed
        self.speed_for_level = ghost_mex_speed
        self.target = (400, 600)
        self.last_target = (400, 600)
        self.mode = Ghost.CHASE
        self.current_direction = HOLD
        self.delay = 0
        self.set_default_mode(False)
        self.random_timer = random_interval
        self.set_delay()

    def reverse_direction(self):
        match self.current_direction:
            case constants.LEFT:
                self.current_direction = constants.RIGHT
            case constants.RIGHT:
                self.current_direction = constants.LEFT
            case constants.UP:
                self.current_direction = constants.DOWN
            case constants.DOWN:
                self.current_direction = constants.UP

    def set_default_mode(self, reverse):
        if self.mode != Ghost.CAUGHT:
            self.texture = ghost_image[self.gtype][HOLD]
            if self.gtype == Ghost.CLYDE:
                self.mode = Ghost.RANDOM
            else:
                self.mode = Ghost.CHASE
            if reverse:
                self.reverse_direction()
            self.speed = self.speed_for_level

    def set_speed_percent(self, perc):
        if 100 >= perc >= 0:
            self.speed = ghost_mex_speed * perc / 100
            self.speed_for_level = self.speed

    def set_scatter_mode(self):
        if self.mode != Ghost.CAUGHT:
            self.mode = Ghost.SCATTER
            self.reverse_direction()

    def set_frightened_mode(self):
        if self.mode != Ghost.CAUGHT:
            if self.mode != Ghost.FRIGHTENED:
                self.speed = self.speed * 0.66
            self.mode = Ghost.FRIGHTENED
            self.texture = frightened
            self.reverse_direction()

    def return_to_pen(self):
        caught_sound.play(volume=0.15)
        self.texture = caught
        self.mode = Ghost.CAUGHT
        self.speed = ghost_mex_speed * 2

    def set_delay(self):
        self.delay = delay_to_release[self.gtype]

    def reduce_delay(self):
        if self.delay > 0:
            self.delay -= 1

    def jump_to_start(self):
        self.center_x = self.start_position[0]
        self.center_y = self.start_position[1]
        self.mode = Ghost.CHASE
        self.set_default_mode(False)
        self.set_delay()
        self.speed = self.speed_for_level
        self.current_direction = HOLD

    def set_direction_image(self, direction):
        if self.mode != Ghost.FRIGHTENED and self.mode != Ghost.CAUGHT:
            self.texture = ghost_image[self.gtype][direction]

    def set_direction(self, pacman):
        if self.delay <= 0:
            if self.current_direction == HOLD:
                self.center_x = Ghost.ghost_exit_point[0]
                self.center_y = Ghost.ghost_exit_point[1]
            match self.mode:
                case Ghost.CHASE:
                    match self.gtype:
                        case Ghost.BLINKY | Ghost.CLYDE:
                            self.target = (pacman.center_x, pacman.center_y)
                        case Ghost.PINKY:
                            match pacman.current_direction:
                                case constants.LEFT | constants.HOLD:
                                    self.target = (
                                        pacman.center_x - 80,
                                        pacman.center_y,
                                    )
                                case constants.RIGHT:
                                    self.target = (
                                        pacman.center_x + 80,
                                        pacman.center_y,
                                    )
                                case constants.UP:
                                    self.target = (
                                        pacman.center_x,
                                        pacman.center_y - 80,
                                    )
                                case constants.DOWN:
                                    self.target = (
                                        pacman.center_x,
                                        pacman.center_y + 80,
                                    )
                        case Ghost.INKY:
                            match pacman.current_direction:
                                case constants.LEFT | constants.HOLD:
                                    self.target = (
                                        pacman.center_x + 80,
                                        pacman.center_y,
                                    )
                                case constants.RIGHT:
                                    self.target = (
                                        pacman.center_x - 80,
                                        pacman.center_y,
                                    )
                                case constants.UP:
                                    self.target = (
                                        pacman.center_x,
                                        pacman.center_y + 80,
                                    )
                                case constants.DOWN:
                                    self.target = (
                                        pacman.center_x,
                                        pacman.center_y - 80,
                                    )
                case Ghost.SCATTER:
                    match self.gtype:
                        case Ghost.BLINKY:
                            self.target = (-200, -100)
                        case Ghost.PINKY:
                            self.target = (WINDOW_WIDTH + 200, -100)
                        case Ghost.INKY:
                            self.target = (-200, WINDOW_HEIGHT + 250)
                        case Ghost.CLYDE:
                            self.target = (WINDOW_WIDTH + 200, WINDOW_HEIGHT + 250)
                case Ghost.RANDOM | Ghost.FRIGHTENED:
                    self.random_timer += 1
                    if self.random_timer >= random_interval - 1:
                        self.last_target = (
                            random.randint(0, WINDOW_WIDTH - 1),
                            random.randint(0, WINDOW_HEIGHT - 1),
                        )
                        self.random_timer = 0
                        self.target = self.last_target
                    if self.mode == Ghost.FRIGHTENED and Ghost.fright_timer < 120:
                        if Ghost.fright_timer % 15 == 0:
                            if self.texture == frightened:
                                self.texture = frightenedW
                            else:
                                self.texture = frightened
                case Ghost.CAUGHT:
                    if (
                        abs(Ghost.ghost_exit_point[0] - self.center_x) < 20
                        and abs(Ghost.ghost_exit_point[1] - self.center_y) < 20
                    ):
                        self.center_x = self.start_position[0]
                        self.center_y = self.start_position[1]
                        self.mode = Ghost.CHASE
                        self.set_default_mode(False)
                        self.current_direction = HOLD
                        self.delay = delay_to_release_after_caught[self.gtype]
                    self.target = Ghost.ghost_exit_point

            tx = self.target[0] - self.center_x
            ty = self.target[1] - self.center_y
            if self.current_direction == HOLD:
                if tx > 0:
                    self.current_direction = RIGHT
                else:
                    self.current_direction = LEFT
            if abs(tx) > abs(ty):
                if self.target[0] > self.center_x:
                    if self.current_direction != LEFT:
                        go_to = RIGHT
                    elif self.target[1] > self.center_y:
                        go_to = UP
                    else:
                        go_to = DOWN
                elif self.current_direction != RIGHT:
                    go_to = LEFT
                elif self.target[1] < self.center_y:
                    go_to = DOWN
                else:
                    go_to = UP
            else:
                if self.target[1] < self.center_y:
                    if self.current_direction != UP:
                        go_to = DOWN
                    elif self.target[0] > self.center_x:
                        go_to = RIGHT
                    else:
                        go_to = LEFT
                elif self.current_direction != DOWN:
                    go_to = UP
                elif self.target[0] > self.center_x:
                    go_to = RIGHT
                else:
                    go_to = LEFT
            return go_to
        else:
            return HOLD

    def get_order(self):
        tx = self.target[0] - self.center_x
        ty = self.center_y - self.target[1]
        if tx > 0 and ty > 0 and abs(tx) > abs(ty):
            order = cycle_order[0]
        elif tx > 0 and ty > 0 and abs(tx) < abs(ty):
            order = cycle_order[4]
        elif tx < 0 and ty > 0 and abs(tx) > abs(ty):
            order = cycle_order[1]
        elif tx < 0 and ty > 0 and abs(tx) < abs(ty):
            order = cycle_order[5]
        elif tx > 0 and ty < 0 and abs(tx) > abs(ty):
            order = cycle_order[2]
        elif tx > 0 and ty < 0 and abs(tx) < abs(ty):
            order = cycle_order[6]
        elif tx < 0 and ty < 0 and abs(tx) > abs(ty):
            order = cycle_order[3]
        else:
            order = cycle_order[7]
        return order
