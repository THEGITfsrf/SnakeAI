import random
import pygame
import numpy as np
import torch
from universal import MultiEnvRLAgent


def cast_ray(head_x, head_y, angle, snake_body, width, height, tile_size):
    import math

    rad = math.radians(angle)
    x, y = head_x, head_y
    max_dist = max(width, height)
    dist = 0

    while 0 <= int(x) < width and 0 <= int(y) < height and (int(x), int(y)) not in snake_body:
        x += math.cos(rad) * tile_size
        y += math.sin(rad) * tile_size
        dist += 1
        if dist >= max_dist:
            break

    return dist / max_dist

# ---------- SnakeGame ----------
class SnakeGame:
    def __init__(self, width=1200, height=800, tile_size=10):
        self.width = width
        self.height = height
        self.tile_size = tile_size

        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Snake AI (Greedy)")
        self.clock = pygame.time.Clock()

        self.reset()

    def reset(self, tile_size=None):
        if tile_size is not None:
            self.tile_size = tile_size
        start_x = self.tile_size
        start_y = self.tile_size
        self.snake_body = [
            (start_x, start_y),
            (start_x - self.tile_size, start_y),
            (start_x - (2 * self.tile_size), start_y),
        ]
        self.direction = "RIGHT"
        self.food = False
        self.food_pos = (None, None)
        self.score = 0
        self.game_over = False
        self.spawn_food()
        return self.get_state()

    def spawn_food(self):
        while True:
            x = random.randrange(0, self.width, self.tile_size)
            y = random.randrange(0, self.height, self.tile_size)
            if (x, y) not in self.snake_body:
                self.food_pos = (x, y)
                self.food = True
                break

    def step(self, action):
        if self.game_over:
            return self.get_state(), 0, True

        turn_left = {"UP": "LEFT", "DOWN": "RIGHT", "LEFT": "DOWN", "RIGHT": "UP"}
        turn_right = {"UP": "RIGHT", "DOWN": "LEFT", "LEFT": "UP", "RIGHT": "DOWN"}

        if action == 1:
            self.direction = turn_left[self.direction]
        elif action == 2:
            self.direction = turn_right[self.direction]

        head_x, head_y = self.snake_body[0]

        if self.direction == "UP":
            new_head = (head_x, head_y - self.tile_size)
        elif self.direction == "DOWN":
            new_head = (head_x, head_y + self.tile_size)
        elif self.direction == "LEFT":
            new_head = (head_x - self.tile_size, head_y)
        else:
            new_head = (head_x + self.tile_size, head_y)

        # collision
        if (
            new_head in self.snake_body[:-1] or
            new_head[0] < 0 or new_head[0] >= self.width or
            new_head[1] < 0 or new_head[1] >= self.height
        ):
            self.game_over = True
            return self.get_state(), -10, True

        reward = 0

        if self.food and new_head == self.food_pos:
            self.snake_body.insert(0, new_head)
            self.score += 1
            reward += 3
            self.food = False
            self.spawn_food()
        else:
            self.snake_body.insert(0, new_head)
            self.snake_body.pop()

        food_x, food_y = self.food_pos
        prev_dist = abs(head_x - food_x) + abs(head_y - food_y)
        new_dist = abs(new_head[0] - food_x) + abs(new_head[1] - food_y)

        reward += 0.02
        if new_head not in self.snake_body[:-1]:
            reward += 0.01 * (prev_dist - new_dist)

        return self.get_state(), reward, False

    def get_state(self):
        head_x, head_y = self.snake_body[0]
        tile = self.tile_size
        dist_left = head_x / self.width
        dist_right = (self.width - head_x) / self.width
        dist_up = head_y / self.height
        dist_down = (self.height - head_y) / self.height

        def danger_at(direction):
            if direction == "UP":
                pos = (head_x, head_y - tile)
            elif direction == "DOWN":
                pos = (head_x, head_y + tile)
            elif direction == "LEFT":
                pos = (head_x - tile, head_y)
            else:
                pos = (head_x + tile, head_y)

            return int(
                pos in self.snake_body
                or pos[0] < 0
                or pos[0] >= self.width
                or pos[1] < 0
                or pos[1] >= self.height
            )

        dir_map = {
            "UP": ["UP", "RIGHT", "LEFT"],
            "DOWN": ["DOWN", "LEFT", "RIGHT"],
            "LEFT": ["LEFT", "UP", "DOWN"],
            "RIGHT": ["RIGHT", "DOWN", "UP"],
        }

        danger = [danger_at(d) for d in dir_map[self.direction]]
        direction_flags = [
            int(self.direction == "LEFT"),
            int(self.direction == "RIGHT"),
            int(self.direction == "UP"),
            int(self.direction == "DOWN"),
        ]

        food_x, food_y = self.food_pos
        food_dx = (food_x - head_x) / self.width
        food_dy = (food_y - head_y) / self.height

        dir_angle_map = {"UP": -90, "RIGHT": 0, "DOWN": 90, "LEFT": 180}
        current_angle = dir_angle_map[self.direction]
        angles = np.linspace(-170, 170, 17)
        ray_values = [
            cast_ray(
                head_x,
                head_y,
                current_angle + angle,
                self.snake_body,
                self.width,
                self.height,
                self.tile_size,
            )
            for angle in angles
        ]

        return np.array(
            danger
            + direction_flags
            + [dist_left, dist_right, dist_up, dist_down, food_dx, food_dy]
            + ray_values,
            dtype=float,
        )

    def render(self):
        self.screen.fill((0, 0, 0))

        for segment in self.snake_body:
            pygame.draw.rect(self.screen, (0, 255, 0),
                             (*segment, self.tile_size, self.tile_size))

        if self.food:
            pygame.draw.rect(self.screen, (255, 0, 0),
                             (*self.food_pos, self.tile_size, self.tile_size))

        pygame.display.flip()
        self.clock.tick(15)  # adjust speed here


# ---------- Load Agent ----------
NUM_ENVS = 1
INPUT_SIZE = 30
OUTPUT_SIZE = 3
HIGH_SCORE_THRESH = 3
TILE_DECREMENT = 5
BASE_TILE = 100
MIN_TILE = 5

agent = MultiEnvRLAgent(
    input_size=INPUT_SIZE,
    output_size=OUTPUT_SIZE,
    num_envs=NUM_ENVS
)

PATH = "snake.pth"
agent.model.load_state_dict(torch.load(PATH, weights_only=True))
agent.model.eval()


# ---------- Run ----------
game = SnakeGame()
states = np.zeros((NUM_ENVS, INPUT_SIZE), dtype=float)
state = game.reset()
states[0] = state

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

    with torch.no_grad():
        state_tensor = torch.tensor(states, dtype=torch.float32).to(agent.device)
        q_values = agent.model(state_tensor)
        actions = torch.argmax(q_values, dim=1).cpu().numpy()

    state, reward, done = game.step(actions[0])
    states[0] = state

    game.render()

    if done:
        print("Score:", game.score)
        pygame.time.wait(500)
        shrink_steps = game.score // HIGH_SCORE_THRESH
        target_tile_size = max(MIN_TILE, BASE_TILE - (shrink_steps * TILE_DECREMENT))
        state = game.reset(tile_size=target_tile_size)
        states[0] = state
