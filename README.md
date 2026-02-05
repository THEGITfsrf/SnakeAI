# Snake2

A classic Snake game built with Python and Pygame. Guide the snake to eat food and grow longer without hitting the walls or yourself.

## Features

- Classic snake gameplay with smooth grid-based movement
- Resizable game window (default 1200x800)
- Checkerboard-style game board
- Score tracking
- Game over screen with Retry and Quit buttons
- Victory condition when the snake fills the entire board
- Custom window icon and font support

## Requirements

- Python 3.x
- Pygame

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/snake-python.git
   cd snake-python
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Ensure the following assets are in the project directory:
   - `snek.png` - window icon
   - `Freedom_Font.TTF` - custom font (falls back to default if missing)

## How to Run

```
python Snake2.py
```

## Controls

| Key | Action |
|-----|--------|
| Arrow Keys | Move the snake (Up, Down, Left, Right) |
| ESC | Quit the game |

## Project Structure

```
.
|-- Snake2.py        # main game script
|-- snek.png         # window icon
|-- Freedom_Font.TTF # custom font
|-- requirements.txt
|-- README.md
```

## License

MIT
