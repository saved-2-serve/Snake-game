#!/usr/bin/env python3
import curses
import random
import time


def clamp(min_value, value, max_value):
    return max(min_value, min(value, max_value))


def place_fruit(snake, height, width):
    while True:
        pos = (random.randint(1, height - 2), random.randint(1, width - 2))
        if pos not in snake:
            return pos


def draw_border(stdscr, top, left, height, width):
    top_left = "┏"
    top_right = "┓"
    bottom_left = "┗"
    bottom_right = "┛"
    horizontal = "━"
    vertical = "┃"
    stdscr.addstr(top, left, top_left)
    stdscr.addstr(top, left + width - 1, top_right)
    stdscr.addstr(top + height - 1, left, bottom_left)
    stdscr.addstr(top + height - 1, left + width - 1, bottom_right)
    for x in range(width):
        if 0 < x < width - 1:
            stdscr.addstr(top, left + x, horizontal)
            stdscr.addstr(top + height - 1, left + x, horizontal)
    for y in range(height):
        if 0 < y < height - 1:
            stdscr.addstr(top + y, left, vertical)
            stdscr.addstr(top + y, left + width - 1, vertical)


def init_colors():
    if not curses.has_colors():
        return {}
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN, -1)
    curses.init_pair(2, curses.COLOR_GREEN, -1)
    curses.init_pair(3, curses.COLOR_YELLOW, -1)
    curses.init_pair(4, curses.COLOR_RED, -1)
    curses.init_pair(5, curses.COLOR_WHITE, -1)
    return {
        "border": curses.color_pair(1),
        "snake_head": curses.color_pair(2) | curses.A_BOLD,
        "snake_body": curses.color_pair(3),
        "fruit": curses.color_pair(4) | curses.A_BOLD,
        "text": curses.color_pair(5),
    }


def draw_game(stdscr, top, left, height, width, snake, fruit, score, speed, paused, colors):
    stdscr.erase()
    if colors:
        stdscr.attron(colors["border"])
    draw_border(stdscr, top, left, height, width)
    if colors:
        stdscr.attroff(colors["border"])
    score_line = f"Score: {score}  Speed: {speed}x  (Arrow keys to move, P to pause, Q to quit)"
    if colors:
        stdscr.addstr(top - 1, left, score_line, colors["text"])
    else:
        stdscr.addstr(top - 1, left, score_line)

    fy, fx = fruit
    fruit_char = "◆"
    if colors:
        stdscr.addstr(top + fy, left + fx, fruit_char, colors["fruit"])
    else:
        stdscr.addstr(top + fy, left + fx, fruit_char)

    for i, (y, x) in enumerate(snake):
        char = "●" if i == 0 else "•"
        if colors:
            color = colors["snake_head"] if i == 0 else colors["snake_body"]
            stdscr.addstr(top + y, left + x, char, color)
        else:
            stdscr.addstr(top + y, left + x, char)

    if paused:
        msg = "PAUSED"
        if colors:
            stdscr.addstr(
                top + height // 2,
                left + (width - len(msg)) // 2,
                msg,
                colors["text"] | curses.A_BOLD,
            )
        else:
            stdscr.addstr(top + height // 2, left + (width - len(msg)) // 2, msg)

    stdscr.refresh()


def wait_for_key(stdscr, prompt):
    stdscr.nodelay(False)
    stdscr.erase()
    stdscr.addstr(0, 0, prompt)
    stdscr.addstr(2, 0, "Press any key to continue.")
    stdscr.refresh()
    stdscr.getch()
    stdscr.nodelay(True)


def game_loop(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.keypad(True)
    colors = init_colors()

    score = 0
    speed = 1
    direction = (0, 1)
    next_direction = direction
    paused = False

    while True:
        rows, cols = stdscr.getmaxyx()
        height = clamp(12, rows - 4, 30)
        width = clamp(20, cols - 2, 50)
        if rows < 16 or cols < 24:
            wait_for_key(stdscr, "Terminal too small. Resize to at least 24x16.")
            continue

        top = max(2, (rows - height) // 2)
        left = max(1, (cols - width) // 2)

        snake = [
            (height // 2, width // 2),
            (height // 2, width // 2 - 1),
            (height // 2, width // 2 - 2),
        ]
        fruit = place_fruit(snake, height, width)
        score = 0
        speed = 1
        direction = (0, 1)
        next_direction = direction
        paused = False

        tick = time.monotonic()
        delay = 0.18

        while True:
            key = stdscr.getch()
            if key in (ord("q"), ord("Q")):
                return
            if key in (ord("p"), ord("P")):
                paused = not paused
            elif key == curses.KEY_UP:
                next_direction = (-1, 0)
            elif key == curses.KEY_DOWN:
                next_direction = (1, 0)
            elif key == curses.KEY_LEFT:
                next_direction = (0, -1)
            elif key == curses.KEY_RIGHT:
                next_direction = (0, 1)

            if paused:
                draw_game(
                    stdscr,
                    top,
                    left,
                    height,
                    width,
                    snake,
                    fruit,
                    score,
                    speed,
                    True,
                    colors,
                )
                time.sleep(0.05)
                continue

            now = time.monotonic()
            if now - tick < delay:
                time.sleep(0.01)
                continue
            tick = now

            if (direction[0] == -next_direction[0]) and (direction[1] == -next_direction[1]):
                next_direction = direction
            direction = next_direction

            head_y, head_x = snake[0]
            new_head = (head_y + direction[0], head_x + direction[1])

            if (
                new_head[0] <= 0
                or new_head[0] >= height - 1
                or new_head[1] <= 0
                or new_head[1] >= width - 1
            ):
                break
            if new_head in snake:
                break

            snake.insert(0, new_head)
            if new_head == fruit:
                score += 1
                if score % 5 == 0:
                    speed += 1
                    delay = max(0.06, delay - 0.015)
                fruit = place_fruit(snake, height, width)
            else:
                snake.pop()

            draw_game(
                stdscr,
                top,
                left,
                height,
                width,
                snake,
                fruit,
                score,
                speed,
                False,
                colors,
            )

        wait_for_key(stdscr, f"Game over! Score: {score}. Press Q to quit or any key to restart.")


def main():
    curses.wrapper(game_loop)


if __name__ == "__main__":
    main()
