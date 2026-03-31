import pygame
import numpy as np
import torch
from universal import MultiEnvRLAgent

# ---------- SnakeGame ----------
class SnakeGame:
    def __init__(self, width=1200, height=800, tile_size=100):
        self.width = width
        self.height = height
        self.tile_size = tile_size

        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Snake AI (Greedy)")
        self.clock = pygame.time.Clock()

        self.reset()

    def reset(self):
        center_x = (self.width // self.tile_size // 2) * self.tile_size
        center_y = (self.height // self.tile_size // 2) * self.tile_size

        self.snake_body = [
            (center_x, center_y),
            (center_x, center_y + self.tile_size),
            (center_x, center_y + 2 * self.tile_size)
        ]

        self.direction = "UP"  # important so it doesn't insta crash
        self.food = False
        self.food_pos = (None, None)
        self.score = 0
        self.game_over = False
        self.spawn_food()
        return self.get_state()
    def spawn_food(self):
        valid_positions = []
        for x in range(0, self.width, self.tile_size):
            for y in range(0, self.height, self.tile_size):
                pos = (x, y)
                if pos not in self.snake_body:
                    valid_positions.append(pos)

        if valid_positions:
            self.food_pos = valid_positions[np.random.randint(len(valid_positions))]
            self.food = True
        else:
            self.game_over = True

    def step(self, action):
        if self.game_over:
            return self.get_state(), 0, True

        directions = ["DOWN","RIGHT","UP","LEFT"]

        # turn logic
        if action == 1:
            idx = directions.index(self.direction)
            self.direction = directions[idx - 1]
        elif action == 2:
            idx = directions.index(self.direction)
            self.direction = directions[(idx + 1) % 4]

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

        # food
        if self.food and new_head == self.food_pos:
            self.snake_body.insert(0, new_head)
            self.score += 1
            self.food = False
            self.spawn_food()
        else:
            self.snake_body.insert(0, new_head)
            self.snake_body.pop()
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
        reward += 0.01 * (prev_dist - new_dist)

        return self.get_state(), reward, False

    def get_state(self):
        head_x, head_y = self.snake_body[0]
        tile = self.tile_size

        directions = [
            (0, -tile),   # UP
            (0, tile),    # DOWN
            (-tile, 0),   # LEFT
            (tile, 0)     # RIGHT
        ]

        ray_data = []

        for dx, dy in directions:
            distance = 0
            food_seen = 0
            body_distance = 0

            x, y = head_x, head_y

            while True:
                x += dx
                y += dy
                distance += 1

                # hit wall
                if x < 0 or x >= self.width or y < 0 or y >= self.height:
                    break

                # food
                if (x, y) == self.food_pos:
                    food_seen = 1

                # body (only first hit matters)
                if (x, y) in self.snake_body and body_distance == 0:
                    body_distance = distance

            # normalize distances
            max_dist = max(self.width, self.height) / tile
            wall_dist = distance / max_dist
            body_dist = (body_distance / max_dist) if body_distance > 0 else 1.0

            ray_data.extend([wall_dist, body_dist, food_seen])

        # --- ORIGINAL FEATURES ---
        direction_flags = [
            int(self.direction == "LEFT"),
            int(self.direction == "RIGHT"),
            int(self.direction == "UP"),
            int(self.direction == "DOWN")
        ]

        food_x, food_y = self.food_pos
        food_flags = [
            int(food_x < head_x),
            int(food_x > head_x),
            int(food_y < head_y),
            int(food_y > head_y)
        ]

        return np.array(ray_data + direction_flags + food_flags, dtype=float)
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
INPUT_SIZE = 20
OUTPUT_SIZE = 3

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
        state = game.reset()
        states[0] = state