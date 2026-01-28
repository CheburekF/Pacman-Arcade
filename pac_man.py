import arcade

from constants import FRAME_REFRESH, HOLD, WINDOW_HEIGHT

player_max_speed = 3.66
caught_timer_default = int(FRAME_REFRESH * 1.5)

life_lost = arcade.load_sound("sounds/lifeLost.wav")
pacman_whole = arcade.load_texture("images/pacWhole.png")

pacman_moving = [
    arcade.load_texture("images/pacOpenLeft.png"),
    arcade.load_texture("images/pacOpenRight.png"),
    arcade.load_texture("images/pacOpenUp.png"),
    arcade.load_texture("images/pacOpenDown.png"),
]

caught_image = [
    arcade.load_texture("images/lost1.png"),
    arcade.load_texture("images/lost2.png"),
    arcade.load_texture("images/lost3.png"),
    arcade.load_texture("images/lost4.png"),
    arcade.load_texture("images/lost5.png"),
    arcade.load_texture("images/lost6.png"),
]


class PacMan(arcade.Sprite):
    def __init__(self, x, y):
        x = x * 20 + 10
        y = WINDOW_HEIGHT - (y * 20 + 40)
        super().__init__(pacman_whole, 18 / 20, x, y)
        self.whole = True
        self.start_position = (x, y)
        self.speed = player_max_speed
        self.speed_for_level = player_max_speed
        self._caught = False
        self.caught_timer = 0
        self.frame_count = 0
        self.current_direction = HOLD
        self.next_direction = HOLD
        self.change_direction = False
        self.done = False

    def set_speed_percent(self, perc):
        if 100 >= perc >= 0:
            self.speed = player_max_speed * perc / 100
            self.speed_for_level = self.speed

    def set_caught(self):
        self._caught = True
        self.next_direction = HOLD
        life_lost.play(volume=0.15)
        self.caught_timer = caught_timer_default
        self.texture = pacman_whole
        self.whole = True

    def caught(self):
        return self._caught

    def return_to_start(self):
        self.center_x = self.start_position[0]
        self.center_y = self.start_position[1]
        self.speed = self.speed_for_level
        self.current_direction = HOLD
        self.texture = pacman_whole
        self.whole = True
        self._caught = False
        self.done = False

    def update(self, delta_time):
        if self._caught:
            self.caught_timer -= 1
            if self.caught_timer <= -6:
                self.done = True
            elif self.caught_timer % 6 == 0:
                self.texture = caught_image[5 - self.caught_timer // 15]
        else:
            if self.current_direction == HOLD:
                self.texture = pacman_whole
            else:
                self.frame_count += 1
                if self.frame_count > 10 or self.change_direction:
                    self.frame_count = 0
                    self.change_direction = False
                    if self.whole:
                        self.texture = pacman_moving[self.current_direction - 1]
                        self.whole = False
                    else:
                        self.texture = pacman_whole
                        self.whole = True
        super().update(delta_time)
