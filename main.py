import arcade
import pyglet
from pyglet.graphics import Batch

from brick import Brick
from dot import Dot
from ghost import Ghost, ghost_score
from maze_grids import maze_layouts
from messages import Message
from pac_man import PacMan

WINDOW_TITLE = "Pacman"
WINDOW_WIDTH = 580
WINDOW_HEIGHT = 700
WINDOW_CENTER = WINDOW_WIDTH / 2
START_LIVES = 3
PAUSED = 0
IN_PLAY = 1
GAME_OVER = 2
END_OF_LEVEL_DELAY = 150
GRID_WIDTH = 20
FRAME_REFRESH = 60
DISPLAY_FRUIT = FRAME_REFRESH * 7
CHASE_TIMER = FRAME_REFRESH * 20
SCATTER_TIMER = FRAME_REFRESH * 10
FRIGHT_TIMER = FRAME_REFRESH * 10
CATCH_TIMER = FRAME_REFRESH * 3
NEW_LIFE_TIMER = FRAME_REFRESH * 3
DELAY = FRAME_REFRESH
NEW_LIFE_INTERVAL = 10000
HOLD = 0
LEFT = 1
RIGHT = 2
UP = 3
DOWN = 4

WHITE = arcade.color.WHITE
GREEN = arcade.color.GREEN
AQUA = arcade.color.AQUA
RED = arcade.color.RED
YELLOW = arcade.color.YELLOW

SCORE_FONT_SIZE = 12
INST_FONT_SIZE = 18
INFO_FONT_SIZE = 16
HEADING_FONT_SIZE = 30

sounds = {
    "music": arcade.load_sound("sounds/MazeTune.mp3"),
    "extra": arcade.load_sound("sounds/extraLife.wav"),
    "game_over": arcade.load_sound("sounds/GameOver.wav"),
    "level": arcade.load_sound("sounds/LevelCompleted.wav"),
    "energiser": arcade.load_sound("sounds/eatEnergiser.wav"),
    "fruit": arcade.load_sound("sounds/eatfruit.wav"),
}


class GameView(arcade.Window):
    def __init__(self):
        super().__init__(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE)
        self.background_color = arcade.csscolor.BLACK
        v = pyglet.display.get_display().get_default_screen()
        self.set_location(
            v.width // 2 - WINDOW_WIDTH // 2, v.height // 2 - WINDOW_HEIGHT // 2
        )

        self.score_batch = Batch()
        self.instructions = Batch()
        self.game_over = Batch()
        self.messages = []
        self.inst = []
        self.game_over_text = []

        self.scene = arcade.Scene()
        for name, spatial in (
            ("Lives", False),
            ("Grid", True),
            ("Dots", False),
            ("Fruit", False),
            ("Ghosts", False),
            ("Pacman", False),
        ):
            self.scene.add_sprite_list(name, spatial)

        self.pacman = None
        self.fruit_position = (0, 0)
        defaults = dict(
            fright_length=0,
            level=0,
            score=0,
            high_score=0,
            dots_eaten=0,
            lives=0,
            new_life_timer=0,
            chase_timer=0,
            scatter_timer=0,
            scatter_count=0,
            new_life_target=0,
            ghosts_eaten=0,
            level_cleared=False,
            end_of_level_timer=0,
            current_ghost_mode=0,
            mode_timer=0,
            fright_counter=0,
            game_state=PAUSED,
            music_playing=None,
        )
        for k, v in defaults.items():
            setattr(self, k, v)

        self.load_high_score()
        self.set_up_score_line()
        self.initialise_new_game()
        self.set_instructions()

    def _text(self, *args, **kwargs):
        return arcade.Text(*args, **kwargs)

    def set_instructions(self):
        lines = [
            "Используйте стрелки, либо WASD для движения",
            "Избегайте попадания в плен к призракам",
            "Собирайте точки и бонусные фрукты",
            "для получения очков",
            "Съедание энерджайзера переводит призраков",
            "в испуганный режим",
            "Ловите призраков в испуганном режиме",
            "для получения очков",
            "Соберите все точки для перехода на",
            "следующий уровень",
            "Маленькая точка = 20   Энерджайзер = 50",
            "Призраки 200–1600   Фрукты 100–5000",
        ]
        y = 620
        self.inst = [
            self._text(
                "Инструкции",
                0,
                y,
                YELLOW,
                HEADING_FONT_SIZE,
                batch=self.instructions,
                width=WINDOW_WIDTH,
                align="center",
                bold=True,
            )
        ]
        y -= 50
        for L in lines:
            self.inst.append(
                self._text(
                    L, 40, y, WHITE, INST_FONT_SIZE, batch=self.instructions, width=600
                )
            )
            y -= 36
        self.inst.append(
            self._text(
                "ПРОБЕЛ — старт без музыки, M — старт с музыкой",
                0,
                y - 50,
                AQUA,
                INST_FONT_SIZE,
                batch=self.instructions,
                width=WINDOW_WIDTH,
                align="center",
            )
        )

    def set_for_level(self):
        self.scatter_count = self.ghosts_eaten = self.dots_eaten = 0
        self.level_cleared = False
        self.create_maze()
        self.pacman.next_direction = HOLD
        self.current_ghost_mode = Ghost.CHASE
        self.mode_timer = CHASE_TIMER
        self.fright_counter = 0
        if self.level < 6:
            sp = 100 - (6 - self.level) * 5
            self.pacman.set_speed_percent(sp)
            for g in self.scene["Ghosts"]:
                g.set_speed_percent(sp)
        self.current_level_text.text = f"Уровень: {self.level}"
        self.set_fruit_line()

    def set_up_score_line(self):
        self.your_score_text = arcade.Text(
            "Ваши очки: 0",
            20,
            WINDOW_HEIGHT - 20,
            WHITE,
            SCORE_FONT_SIZE,
            batch=self.score_batch,
        )
        self.high_score_text = arcade.Text(
            f"Рекорд: {self.high_score}",
            200,
            WINDOW_HEIGHT - 20,
            WHITE,
            SCORE_FONT_SIZE,
            batch=self.score_batch,
        )
        self.current_level_text = arcade.Text(
            "Уровень: 1",
            400,
            WINDOW_HEIGHT - 20,
            WHITE,
            SCORE_FONT_SIZE,
            batch=self.score_batch,
        )

    def set_game_over(self):
        self.game_over = Batch()
        y = 500
        self.game_over_text = [
            self._text(
                "ИГРА ОКОНЧЕНА",
                0,
                y,
                YELLOW,
                HEADING_FONT_SIZE,
                batch=self.game_over,
                width=WINDOW_WIDTH,
                align="center",
                bold=True,
            ),
            self._text(
                f"Ваши очки: {self.score}",
                0,
                y - 75,
                WHITE,
                HEADING_FONT_SIZE,
                batch=self.game_over,
                width=WINDOW_WIDTH,
                align="center",
            ),
            self._text(
                f"Вы достигли уровня: {self.level}",
                0,
                y - 150,
                WHITE,
                HEADING_FONT_SIZE,
                batch=self.game_over,
                width=WINDOW_WIDTH,
                align="center",
            ),
        ]
        if self.score > self.high_score:
            self.high_score = self.score
            with open("scores.txt", "w") as f:
                f.write(str(self.score))
            self.game_over_text.append(
                self._text(
                    "Поздравляем, новый рекорд!",
                    0,
                    y - 225,
                    GREEN,
                    HEADING_FONT_SIZE,
                    batch=self.game_over,
                    width=WINDOW_WIDTH,
                    align="center",
                )
            )
        self.game_over_text.append(
            self._text(
                "ПРОБЕЛ — старт без музыки, M — старт с музыкой",
                0,
                y - 285,
                AQUA,
                INST_FONT_SIZE,
                batch=self.game_over,
                width=WINDOW_WIDTH,
                align="center",
            )
        )

    def load_high_score(self):
        try:
            with open("scores.txt", "r") as f:
                self.high_score = int(f.read())
        except Exception:
            self.high_score = 0

    def initialise_new_game(self):
        self.score = 0
        self.level = 1
        self.lives = START_LIVES
        self.chase_timer = CHASE_TIMER
        self.scatter_timer = SCATTER_TIMER
        self.fright_length = FRIGHT_TIMER
        self.new_life_target = NEW_LIFE_INTERVAL
        self.set_for_level()
        self.set_lives_line()
        self.set_fruit_line()

    def set_lives_line(self):
        self.scene["Lives"].clear()
        for i in range(self.lives):
            s = arcade.Sprite("images/pacOpen.png")
            s.center_x = 44 + i * 25
            s.center_y = 25
            self.scene.add_sprite("Lives", s)

    def set_fruit_line(self):
        self.scene["Fruit"].clear()
        for i in range(self.level):
            f = arcade.Sprite(Dot.fruit_image[i])
            f.center_x = WINDOW_WIDTH - i * 25 - 40
            f.center_y = 25
            self.scene.add_sprite("Fruit", f)

    def add_new_life(self):
        if self.lives < 5:
            self.lives += 1
            self.messages.append(
                Message("Новая жизнь", (0, 15), RED, INST_FONT_SIZE, 100, True)
            )
            self.set_lives_line()
            sounds["extra"].play(volume=0.15)

    def create_maze(self):
        self.scene["Grid"].clear()
        self.scene["Dots"].clear()
        self.scene["Ghosts"].clear()
        level = (self.level - 1) % len(maze_layouts)
        for y, row in enumerate(maze_layouts[level]):
            for x, c in enumerate(row):
                if c == "X":
                    self.scene.add_sprite("Grid", Brick(level, x, y))
                elif c == "O":
                    self.scene.add_sprite("Grid", Brick(Brick.OPENING, x, y))
                elif c == "Y":
                    if self.pacman is not None:
                        self.pacman.kill()
                    self.pacman = PacMan(x, y)
                    self.scene.add_sprite("Pacman", self.pacman)
                elif c == ".":
                    self.scene.add_sprite("Dots", Dot(Dot.DOT, x, y))
                elif c == "E":
                    self.scene.add_sprite("Dots", Dot(Dot.ENERGISER, x, y))
                elif c == "F":
                    self.fruit_position = (x, y)
                elif c == "B":
                    self.scene.add_sprite("Ghosts", Ghost(Ghost.BLINKY, x, y))
                elif c == "I":
                    self.scene.add_sprite("Ghosts", Ghost(Ghost.INKY, x, y))
                elif c == "P":
                    self.scene.add_sprite("Ghosts", Ghost(Ghost.PINKY, x, y))
                elif c == "C":
                    self.scene.add_sprite("Ghosts", Ghost(Ghost.CLYDE, x, y))

    def update_score(self, points):
        self.score += points
        self.your_score_text.text = f"Ваши очки: {self.score}"
        if self.score >= self.new_life_target:
            self.new_life_target += NEW_LIFE_INTERVAL
            self.add_new_life()

    def snap_to_grid(self, pos, speed):
        ip = round(pos)
        base = (ip // 20) * 20
        dist = pos - base
        t = speed / 1.5
        if dist >= 20 - t:
            return ip + 20 - ip % 20
        if dist <= t:
            return ip - ip % 20
        return pos

    def try_to_move(self, direction, obj):
        if direction != obj.current_direction:
            obj.center_x = self.snap_to_grid(obj.center_x, obj.speed)
            obj.center_y = self.snap_to_grid(obj.center_y, obj.speed)
        vx = obj.speed if direction == RIGHT else -obj.speed if direction == LEFT else 0
        vy = obj.speed if direction == UP else -obj.speed if direction == DOWN else 0
        obj.center_x += vx
        obj.center_y += vy
        hits = arcade.check_for_collision_with_list(obj, self.scene["Grid"])
        if hits:
            b = hits[0]
            if direction == LEFT:
                obj.center_x = b.center_x + 20
            elif direction == RIGHT:
                obj.center_x = b.center_x - 20
            elif direction == UP:
                obj.center_y = b.center_y - 20
            elif direction == DOWN:
                obj.center_y = b.center_y + 20
            return False
        if obj.current_direction != direction:
            obj.current_direction = direction
            obj.change_direction = True
        return True

    def move_pacman(self, nd):
        if not self.try_to_move(nd, self.pacman):
            self.try_to_move(self.pacman.current_direction, self.pacman)
        if self.pacman.center_x < 2:
            self.pacman.center_x = WINDOW_WIDTH - 22
        elif self.pacman.center_x > WINDOW_WIDTH - 22:
            self.pacman.center_x = 2

    def move_ghost(self, ghost, direction):
        if not self.try_to_move(direction, ghost):
            return False
        ghost.set_direction_image(direction)
        if ghost.center_x < 2:
            ghost.center_x = WINDOW_WIDTH - 22
        elif ghost.center_x > WINDOW_WIDTH - 22:
            ghost.center_x = 2
        return True

    def ghost_fright_over(self):
        self.ghosts_eaten = 0
        for g in self.scene["Ghosts"]:
            g.set_default_mode(False)
        self.mode_timer = self.chase_timer

    def change_ghost_mode(self):
        if self.scatter_count < 3 and self.current_ghost_mode == Ghost.CHASE:
            self.scatter_count += 1
            self.current_ghost_mode = Ghost.SCATTER
            self.mode_timer = self.scatter_timer
            for g in self.scene["Ghosts"]:
                g.set_scatter_mode()
        else:
            self.current_ghost_mode = Ghost.CHASE
            self.mode_timer = self.chase_timer
            for g in self.scene["Ghosts"]:
                g.set_default_mode(False)

    def on_key_press(self, key, modifiers):
        if key in (arcade.key.LEFT, arcade.key.A):
            self.pacman.next_direction = LEFT
        elif key in (arcade.key.RIGHT, arcade.key.D):
            self.pacman.next_direction = RIGHT
        elif key in (arcade.key.UP, arcade.key.W):
            self.pacman.next_direction = UP
        elif key in (arcade.key.DOWN, arcade.key.S):
            self.pacman.next_direction = DOWN
        elif key == arcade.key.SPACE and self.game_state != IN_PLAY:
            self.initialise_new_game()
            self.game_state = IN_PLAY
        elif key == arcade.key.M and self.game_state != IN_PLAY:
            self.initialise_new_game()
            self.game_state = IN_PLAY
            self.music_playing = sounds["music"].play(volume=0.33, loop=True)

    def check_if_eaten_dot(self):
        hits = arcade.check_for_collision_with_list(self.pacman, self.scene["Dots"])
        if not hits:
            return
        dot = hits[0]
        self.update_score(dot.score)
        dot.done = True
        self.dots_eaten += 1
        for g in self.scene["Ghosts"]:
            g.reduce_delay()
        if dot.dtype == Dot.ENERGISER:
            sounds["energiser"].play(volume=0.15)
            for g in self.scene["Ghosts"]:
                g.set_frightened_mode()
            Ghost.fright_timer = self.fright_length
        elif dot.dtype == Dot.FRUIT:
            sounds["fruit"].play(volume=0.15)
            self.messages.append(
                Message(
                    f"{dot.score}",
                    (dot.center_x - 10, dot.center_y - 5),
                    WHITE,
                    SCORE_FONT_SIZE,
                    100,
                    False,
                )
            )
        if self.dots_eaten in (70, 170):
            self.scene.add_sprite(
                "Dots",
                Dot(
                    Dot.FRUIT,
                    self.fruit_position[0],
                    self.fruit_position[1],
                    self.level,
                ),
            )

    def check_if_ghost_collide(self):
        hits = arcade.check_for_collision_with_list(self.pacman, self.scene["Ghosts"])
        if not hits:
            return
        ghost = hits[0]
        if ghost.mode == Ghost.FRIGHTENED:
            if self.ghosts_eaten < 4:
                self.ghosts_eaten += 1
            pts = ghost_score[self.ghosts_eaten - 1]
            self.update_score(pts)
            self.messages.append(
                Message(
                    f"{pts}",
                    (ghost.center_x - 10, ghost.center_y - 5),
                    WHITE,
                    SCORE_FONT_SIZE,
                    100,
                    False,
                )
            )
            ghost.return_to_pen()
        elif ghost.mode != Ghost.CAUGHT:
            self.pacman.set_caught()
            self.lives -= 1
            self.set_lives_line()

    def on_update(self, delta_time):
        if self.game_state != IN_PLAY:
            return
        if self.pacman.done:
            if self.lives < 1:
                self.set_game_over()
                self.game_state = GAME_OVER
                if self.music_playing is not None:
                    arcade.stop_sound(self.music_playing)
                sounds["game_over"].play(volume=0.05)
            else:
                self.pacman.return_to_start()
                self.pacman.next_direction = HOLD
                for g in self.scene["Ghosts"]:
                    g.jump_to_start()
                self.ghost_fright_over()
            return

        if (
            not self.level_cleared
            and self.pacman.next_direction != HOLD
            and not self.pacman.caught()
        ):
            self.move_pacman(self.pacman.next_direction)

        self.check_if_eaten_dot()

        if not self.pacman.caught():
            if len(self.scene["Dots"]) == 0:
                if not self.level_cleared:
                    self.level_cleared = True
                    self.end_of_level_timer = END_OF_LEVEL_DELAY
                    sounds["level"].play(volume=0.15)
                self.end_of_level_timer -= 1
                if self.end_of_level_timer <= 0:
                    self.level += 1
                    self.set_for_level()
                    self.chase_timer += FRAME_REFRESH * 2
                    if self.scatter_timer > FRIGHT_TIMER * 5:
                        self.scatter_timer -= FRAME_REFRESH / 2
                    if self.fright_length > FRAME_REFRESH * 5:
                        self.fright_length -= FRAME_REFRESH / 2
                else:
                    return

            self.check_if_ghost_collide()

            if Ghost.fright_timer > 0:
                Ghost.fright_timer -= 1
                if Ghost.fright_timer <= 0:
                    self.ghost_fright_over()
            else:
                self.mode_timer -= 1
                if self.mode_timer <= 0:
                    self.change_ghost_mode()

            for ghost in self.scene["Ghosts"]:
                d = ghost.set_direction(self.pacman)
                if not self.move_ghost(ghost, d):
                    if not self.move_ghost(ghost, ghost.current_direction):
                        order = ghost.get_order()
                        moved = False
                        for o in order:
                            if (
                                (o == LEFT and ghost.current_direction == RIGHT)
                                or (o == RIGHT and ghost.current_direction == LEFT)
                                or (o == UP and ghost.current_direction == DOWN)
                                or (o == DOWN and ghost.current_direction == UP)
                            ):
                                continue
                            if self.move_ghost(ghost, o):
                                moved = True
                                break
                        if not moved:
                            alt = {LEFT: RIGHT, RIGHT: LEFT, UP: DOWN, DOWN: UP}
                            self.move_ghost(
                                ghost, alt.get(ghost.current_direction, LEFT)
                            )

        self.scene.update(delta_time)

    def on_draw(self):
        self.clear()
        if self.game_state == IN_PLAY:
            self.scene.draw()
            for m in list(self.messages):
                m.draw()
                if m.done:
                    self.messages.remove(m)
        if self.game_state == IN_PLAY:
            self.score_batch.draw()
        elif self.game_state == GAME_OVER:
            self.game_over.draw()
        elif self.game_state == PAUSED:
            self.instructions.draw()


def main():
    GameView()
    arcade.run()


if __name__ == "__main__":
    main()
