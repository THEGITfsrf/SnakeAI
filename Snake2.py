import random
import numpy as np
from universal import MultiEnvRLAgent
import torch
from tqdm import tqdm
from collections import deque
import matplotlib.pyplot as plt
def cast_ray(head_x, head_y, angle, snake_body, width, height, tile_size):
    # angle in degrees
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
    return dist / max_dist  # normalize 0-1
class SnakeGame:
    def __init__(self, width=1200, height=800, tile_size=100):
        self.width = width
        self.height = height
        self.tile_size = tile_size
        self.steps_since_high = 0
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
            if (x,y) not in self.snake_body:
                self.food_pos = (x,y)
                self.food = True
                break
    def step(self, action):
        if self.game_over:
            return self.get_state(), 0, True
        directions = ["DOWN","RIGHT","UP","LEFT"]
        turn_left = { "UP":"LEFT", "DOWN":"RIGHT", "LEFT":"DOWN", "RIGHT":"UP" }
        turn_right = { "UP":"RIGHT", "DOWN":"LEFT", "LEFT":"UP", "RIGHT":"DOWN" }
        # --- direction logic (no reverse) ---
        if action == 0:
            self.direction = self.direction
        if action == 1:  # turn left
            self.direction = turn_left[self.direction]
        elif action == 2:  # turn right
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

        reward = 0

        # --- collision ---
        if (
            new_head in self.snake_body[:-1] or
            new_head[0] < 0 or new_head[0] >= self.width or
            new_head[1] < 0 or new_head[1] >= self.height
        ):
            reward -= 8
            return self.get_state(), reward, True
        
        # --- food ---
        if self.food and new_head == self.food_pos:
            self.snake_body.insert(0, new_head)
            self.score += 1
            reward += 3  # small linear growth
            self.food = False
            self.spawn_food()
        else:
            self.snake_body.insert(0, new_head)
            self.snake_body.pop()
        food_x, food_y = self.food_pos
        reward += 0.02  # tiny reward for surviving a step
        prev_dist = abs(head_x - food_x) + abs(head_y - food_y)
        new_dist = abs(new_head[0] - food_x) + abs(new_head[1] - food_y)

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
        # --- DANGER ---
        # Check if moving straight / right / left will hit wall or self
        def danger_at(direction):
            if direction == "UP":
                pos = (head_x, head_y - tile)
            elif direction == "DOWN":
                pos = (head_x, head_y + tile)
            elif direction == "LEFT":
                pos = (head_x - tile, head_y)
            else:
                pos = (head_x + tile, head_y)

            return int(pos in self.snake_body or pos[0] < 0 or pos[0] >= self.width or pos[1] < 0 or pos[1] >= self.height)

        # Map relative moves to absolute directions
        dir_map = {
            "UP": ["UP", "RIGHT", "LEFT"],
            "DOWN": ["DOWN", "LEFT", "RIGHT"],
            "LEFT": ["LEFT", "UP", "DOWN"],
            "RIGHT": ["RIGHT", "DOWN", "UP"]
        }

        danger = [danger_at(d) for d in dir_map[self.direction]]  # straight, right, left

        # --- CURRENT DIRECTION ---
        direction_flags = [
            int(self.direction == "LEFT"),
            int(self.direction == "RIGHT"),
            int(self.direction == "UP"),
            int(self.direction == "DOWN")
        ]

        # --- FOOD LOCATION ---
        food_x, food_y = self.food_pos
        food_flags = [
            int(food_x < head_x),  # food left
            int(food_x > head_x),  # food right
            int(food_y < head_y),  # food up
            int(food_y > head_y)   # food down
        ]
        dir_angle_map = {"UP": -90, "RIGHT": 0, "DOWN": 90, "LEFT": 180}
        current_angle = dir_angle_map[self.direction]
        angles = np.linspace(-170, 170, 17)  # more rays
        ray_values = [cast_ray(head_x, head_y, current_angle + a, self.snake_body, self.width, self.height, self.tile_size) for a in angles]
        food_dx = (food_x - head_x) / self.width   # -1 to 1
        food_dy = (food_y - head_y) / self.height  # -1 to 1
        state = danger + direction_flags + [dist_left, dist_right, dist_up, dist_down, food_dx, food_dy] + ray_values
        return np.array(state, dtype=float)

NUM_ENVS = 64
INPUT_SIZE = 30
OUTPUT_SIZE = 3
WINDOW = 100  # rolling window for min/max logging
HIGH_SCORE_THRESH = 3   # score to trigger tile shrink
TILE_DECREMENT = 5    # reduce tile size by this
BASE_TILE = 100
MIN_TILE = 5          # don’t go too small
states = np.zeros((NUM_ENVS, INPUT_SIZE), dtype=np.float32)
rewards = [0] * NUM_ENVS
dones = [False] * NUM_ENVS
truncs = [False] * NUM_ENVS
games = [SnakeGame() for _ in range(NUM_ENVS)]
GAMES = 100_000

# --- Load Agent in FP16 on GPU ---
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
agent = MultiEnvRLAgent(input_size=INPUT_SIZE, output_size=OUTPUT_SIZE, num_envs=NUM_ENVS)
agent.model.to(device)  # convert model to FP16

# ------------- Logging ----------------
high_score = 0
episode_scores = []
rolling_scores = deque(maxlen=WINDOW)
rolling_min_log = []
rolling_max_log = []
sim_steps = 0
try:
    for episode in tqdm(range(GAMES)):
        done_flags = [False] * NUM_ENVS

        while not all(done_flags):
            # convert states to float16 tensor for FP16 inference
            states_tensor = torch.tensor(states, dtype=torch.float32, device=device)
            actions = agent.step(states_tensor.cpu().numpy(), rewards, dones, truncs)

            for i, game in enumerate(games):
                if done_flags[i]:
                    continue

                state, reward, done = game.step(actions[i])
                sim_steps += 1

                states[i] = state
                rewards[i] = reward
                dones[i] = done
                done_flags[i] = done

                if game.score > high_score:
                    high_score = game.score
                    print(f"new high score: {high_score}")

        # record last game's score
        score = game.score
        episode_scores.append(score)
        rolling_scores.append(score)

        # rolling min/max logging
        if len(rolling_scores) == WINDOW:
            rolling_min_log.append(min(rolling_scores))
            rolling_max_log.append(max(rolling_scores))

        # before your main loop
        

        # inside your reset loop, after game ends:
        # inside the reset loop, after each game ends
        for i, game in enumerate(games):
            shrink_steps = game.score // HIGH_SCORE_THRESH
            target_tile_size = max(MIN_TILE, BASE_TILE - (shrink_steps * TILE_DECREMENT))
            if target_tile_size != game.tile_size:
                game.tile_size = target_tile_size
                print(f"env {i} set to {game.tile_size} at score {game.score}")
            states[i] = game.reset(tile_size=game.tile_size)
            rewards[i] = 0
            dones[i] = False
            truncs[i] = False

        if episode % 10 == 0:
            tile_sizes = [g.tile_size for g in games]
            print(f"Episode {episode}, high_score: {high_score}, tile sizes min/max: {min(tile_sizes)}/{max(tile_sizes)}")

except KeyboardInterrupt:
    print("Saving model due to interrupt...")

# ------------- Total Simulated Time ----------------
total_seconds = sim_steps / 30  # 30 steps per sec
seconds = int(total_seconds % 60)
minutes = int((total_seconds // 60) % 60)
hours = int((total_seconds // 3600) % 24)
days = int((total_seconds // (3600*24)) % 30)
months = int((total_seconds // (3600*24*30)) % 12)
years = int(total_seconds // (3600*24*30*12))

print(f"Simulated time: {years:02}/{months:02}/{days:02}/{hours:02}/{minutes:02}/{seconds:02}")
print(f"High score achieved: {high_score}")

# ------------- Save Model ----------------
PATH = "snake.pth"
torch.save(agent.model.state_dict(), PATH)

# ------------- Plot ----------------
episodes = np.arange(len(episode_scores))
coeffs = np.polyfit(episodes, episode_scores, 3)
trend = np.polyval(coeffs, episodes)

plt.figure(figsize=(12,6))
plt.plot(episodes, episode_scores, alpha=0.3, label="Score per episode")
plt.plot(episodes, trend, color='red', linewidth=2, label="Trend line (best fit)")
plt.plot(np.arange(WINDOW-1, len(rolling_min_log)+WINDOW-1), rolling_min_log, color='blue', label="Rolling min (last 100)")
plt.plot(np.arange(WINDOW-1, len(rolling_max_log)+WINDOW-1), rolling_max_log, color='green', label="Rolling max (last 100)")
plt.xlabel("Episode")
plt.ylabel("Score")
plt.title("Snake Agent Growth Over Time")
plt.legend()
plt.show()
