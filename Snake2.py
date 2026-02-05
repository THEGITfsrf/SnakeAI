import pygame 

import random

# initialization
pygame.init()
screen = pygame.display.set_mode((1200, 800),pygame.RESIZABLE)
img_icon = pygame.image.load("snek.png")
pygame.display.set_icon(img_icon)
pygame.display.set_caption("Snake2")
clock = pygame.time.Clock()
running = True

direction_changed_this_tick = False

food_pos = (None, None)
food = False

score = 0
high_score = 0

tile_size = 100
color_light = (170, 215, 81)
color_dark = (162, 209, 73)

snake_body = [(100, 100), (100, 200), (100, 300)]
direction = "RIGHT"
game_over = False
font_path = "Freedom_Font.ttf" 

def draw_checkerboard(surface):
    width, height = surface.get_size()
    for y in range(0, height, tile_size):
        for x in range(0, width, tile_size):
            is_light = (x // tile_size + y // tile_size) % 2 == 0
            color = color_light if is_light else color_dark
            pygame.draw.rect(surface, color, (x, y, tile_size, tile_size))

def draw_snake(surface):
    global direction
    
    for segment in snake_body:
        pygame.draw.rect(surface, (21, 18, 224), (segment[0], segment[1], tile_size, tile_size))

def draw_game_over(surface):
    width, height = surface.get_size()
    center_x, center_y = width // 2, height // 2
    
    try:
        font_large = pygame.font.Font(font_path, 150)
        font_btn = pygame.font.Font(font_path, 50)
    except:
        font_large = pygame.font.Font(None, 200)
        font_btn = pygame.font.Font(None, 50)
    
    text = font_large.render("Game Over", True, (255, 0, 0))
    text_rect = text.get_rect(center=(center_x, center_y - 80))
    surface.blit(text, text_rect)
    
    # button dimensions
    btn_w, btn_h = 200, 60
    retry_rect = pygame.Rect(center_x - btn_w - 20, center_y + 20, btn_w, btn_h)
    quit_rect = pygame.Rect(center_x + 20, center_y + 20, btn_w, btn_h)
    
    pygame.draw.rect(surface, (50, 150, 50), retry_rect)
    pygame.draw.rect(surface, (150, 50, 50), quit_rect)
    
    retry_text = font_btn.render("Retry", True, (255, 255, 255))
    quit_text = font_btn.render("Quit", True, (255, 255, 255))
    surface.blit(retry_text, retry_text.get_rect(center=retry_rect.center))
    surface.blit(quit_text, quit_text.get_rect(center=quit_rect.center))

    return retry_rect, quit_rect

def draw_victory(surface):
    try:
        font = pygame.font.Font(font_path, 150)
    except:
        font = pygame.font.Font(None, 200)
    text = font.render("VICTORY", True, (255, 0, 0))
    text_rect = text.get_rect(center=(surface.get_width() // 2, surface.get_height() // 2))
    surface.blit(text, text_rect)

def move_snake():


    global snake_body, running, game_over, food, food_pos, score, direction_changed_this_tick
    head_x, head_y = snake_body[0]
    
    if direction == "UP":
        new_head = (head_x, head_y - tile_size)
    elif direction == "DOWN":
        new_head = (head_x, head_y + tile_size)
    elif direction == "LEFT":
        new_head = (head_x - tile_size, head_y)
    elif direction == "RIGHT":
        new_head = (head_x + tile_size, head_y)
    
    screen_width, screen_height = screen.get_size()
    
    if new_head in snake_body[:-1]:
        game_over = True
        return

    if food and food_pos[0] is not None and new_head == (food_pos[0], food_pos[1]):
        snake_body.insert(0, new_head)

        score += 1
        food = False
        return

    if new_head[0] < 0 or new_head[0] >= screen_width or new_head[1] < 0 or new_head[1] >= screen_height:
        game_over = True
    else:
        snake_body.insert(0, new_head)
        snake_body.pop()
    direction_changed_this_tick = False
    
def reset_game():
    global snake_body, direction, game_over, food, food_pos, score, direction_changed_this_tick

    snake_body = [(100, 100), (100, 200), (100, 300)]
    direction = "RIGHT"
    game_over = False
    food = False
    direction_changed_this_tick = False
    food_pos = (None, None)
    score = 0

def spawn_food(surface):
    global food_pos, food

    width, height = surface.get_size()
    valid_positions = []
    if food == False:
        for x in range(0,width,tile_size):
            for y in range(0,height,tile_size):
                pos = (x,y)
                if pos not in snake_body:
                    valid_positions.append(pos)
        if valid_positions:
            food_pos = random.choice(valid_positions)
            draw_food(surface)
            food = True
        else:
            food_pos = (None, None)
            draw_victory(screen)
            running = False

def draw_food(surface):
    global food_pos
    pygame.draw.rect(surface, (250, 126, 2), (food_pos[0], food_pos[1], tile_size, tile_size))

def draw_score(surface):
    try:
        font = pygame.font.Font(font_path, 50)
    except:
        font = pygame.font.Font(None, 50)
    text = font.render(f"Score: {score}", True, (255, 255, 255))
    text_rect = text.get_rect(center=(surface.get_width() // 2, 100))
    surface.blit(text, text_rect)
# Game loop
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if event.key == pygame.K_UP:
                if direction_changed_this_tick == False and direction != "DOWN":
                    direction = "UP"
                    direction_changed_this_tick = True

            if event.key == pygame.K_DOWN:
                if direction_changed_this_tick == False and direction != "UP":
                    direction = "DOWN"
                    direction_changed_this_tick = True

            if event.key == pygame.K_LEFT:
                if direction_changed_this_tick == False and direction != "RIGHT":
                    direction = "LEFT"
                    direction_changed_this_tick = True

            if event.key == pygame.K_RIGHT:
                if direction_changed_this_tick == False and direction != "LEFT":
                    direction = "RIGHT"
                    direction_changed_this_tick = True

    

    if not game_over:
        move_snake()
    
    draw_checkerboard(screen)
    draw_snake(screen)
    spawn_food(screen)

    if food and food_pos[0] is not None:    
        draw_food(screen)
    draw_score(screen)
    

    
    if game_over:
        retry_rect, quit_rect = draw_game_over(screen)
        pygame.display.flip()
        
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # left click
                        pos = pygame.mouse.get_pos()
                        if retry_rect.collidepoint(pos):
                            reset_game()
                            waiting = False
                        elif quit_rect.collidepoint(pos):
                            waiting = False
                            running = False
            clock.tick(30)
    else:
        pygame.display.flip()
        clock.tick(5)

# Quit Pygame
pygame.quit()