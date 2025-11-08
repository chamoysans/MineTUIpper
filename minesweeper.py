import keyboard
import os
import sys
import subprocess
from colorama import init, Back, Style, Fore

init(autoreset=True)

# CONFIGURATION

num_bombs = "default"
gridsize = [13, 13]  # width=6, height=7
spacing = 2

# DO NOT TOUCH ANYTHING AFTER THIS POINT

player = {
    "pos": [
        (gridsize[0]//2),
        (gridsize[1]//2)
    ]
}

if num_bombs == "default":
    totaltiles = gridsize[0]*gridsize[1]
    num_bombs = totaltiles//7

#centprint stuff
import re
from shutil import get_terminal_size

# try to use wcwidth for correct unicode width (emojis, east-asian chars)
try:
    from wcwidth import wcswidth
except Exception:
    wcswidth = None

ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')  # strips colorama / ANSI SGR codes

def visible_width(s: str) -> int:
    """Return the visible terminal width of s (strips ANSI; uses wcwidth if available)."""
    clean = ANSI_RE.sub('', s)           # remove ANSI escape sequences
    if wcswidth:
        w = wcswidth(clean)
        return w if w >= 0 else len(clean)  # wcwidth returns -1 on unprintable; fallback
    return len(clean)

def centprint(s: str):
    # recalc terminal width every call (handles resize)
    width = get_terminal_size().columns
    vis = visible_width(s)
    pad = (width - vis) // 2
    if pad <= 0:
        print(s)   # line too wide or exact fit
    else:
        print(" " * pad + s)

grid = []

CSI = "\x1b["

NotDeadL = True
NotDead = True

def clear_and_home(clear):
    # hide cursor (optional), go home
    # sys.stdout.write(CSI + "?25l")   # hide cursor (optional)
    sys.stdout.write(CSI + "H")       # move cursor home
    # optionally clear from cursor to end of screen:
    if bool(clear):
        sys.stdout.write(CSI + "J")       # erase below


for i in range(gridsize[1]):  # rows
    row = []
    for j in range(gridsize[0]):  # columns
        row.append([0, 0])  # [sweeped/flagged, safe]

        #[0] being 0 means unsweeped, and it being 1 means sweeped, being 2 means flagged
        #[1]:
        # - 0 means safe
        # - 1 means bomb
        #[2] (only appears when [1] is 0):
        # - literally just the bomb count
    
    grid.append(row)  # add the row to the grid



# make map

import random

WIDTH, HEIGHT = gridsize[0], gridsize[1]

import random

def makemap(safe_x, safe_y):
    """
    Place bombs excluding the 3x3 safe zone around (safe_x, safe_y),
    then compute integer neighbor counts into cell[2] for all safe cells.
    """
    # Clear any existing bombs/counts just in case (useful if makemap called multiple times)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            grid[y][x][1] = 0   # no bomb
            # ensure slot for count exists and is integer 0
            if len(grid[y][x]) > 2:
                grid[y][x][2] = 0
            else:
                # if only [state, safe], extend to have count at index 2
                grid[y][x].append(0)

    # build available coords excluding the 3x3 safe zone
    safe_zone = set()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            nx, ny = safe_x + dx, safe_y + dy
            if 0 <= nx < WIDTH and 0 <= ny < HEIGHT:
                safe_zone.add((nx, ny))

    all_coords = [(x, y) for y in range(HEIGHT) for x in range(WIDTH) if (x, y) not in safe_zone]

    # if num_bombs is too large for available slots, clamp it
    n_bombs = min(num_bombs, len(all_coords))
    bomb_coords = random.sample(all_coords, n_bombs)

    for bx, by in bomb_coords:
        grid[by][bx][1] = 1  # mark bomb

    # compute neighbor counts (integers, 0..8)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if grid[y][x][1] == 1:
                grid[y][x][2] = -1   # optional sentinel for bombs if you want
                continue
            count = 0
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < WIDTH and 0 <= ny < HEIGHT:
                        if grid[ny][nx][1] == 1:
                            count += 1
            grid[y][x][2] = count  # integer 0..8

# flood fill

from collections import deque

def flood_fill(sx, sy):
    """
    Iterative BFS flood-fill revealing contiguous zero-count areas.
    Reveals the start cell and expands to neighbors when count == 0.
    """
    if not (0 <= sx < WIDTH and 0 <= sy < HEIGHT):
        return

    q = deque()
    q.append((sx, sy))
    while q:
        x, y = q.popleft()
        cell = grid[y][x]
        # skip if already revealed or flagged
        if cell[0] == 1 or cell[0] == 2:
            continue

        # reveal
        cell[0] = 1

        # get numeric count (bombs store -1 or 1 in grid[*][*][1])
        cnt = cell[2] if len(cell) > 2 else 0

        # only expand if this is a zero neighbor cell
        if cnt == 0:
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < WIDTH and 0 <= ny < HEIGHT:
                        neigh = grid[ny][nx]
                        # if neighbor not revealed and not flagged and not a bomb, add to queue
                        if neigh[0] != 1 and neigh[0] != 2 and neigh[1] == 0:
                            q.append((nx, ny))


countcol = [
    "",
    Style.BRIGHT + Fore.BLUE, #1
    Fore.GREEN, #2
    Style.BRIGHT + Fore.RED, #3
    Fore.BLUE, #4
    Fore.RED, #5
    Fore.CYAN, #6
    Style.BRIGHT + Fore.BLACK, #7
    
]



def main():
    global NotDead
    global NotDeadL


    # grid rendering
    centprint("MINETUIIPER")
    centprint("┏" + ("━" * (WIDTH*(1+spacing)+spacing) + "┓"))
    for k in range(((spacing-1)//2)):
        centprint("┃" + (" " * (WIDTH*(1+spacing)+spacing)) + "┃")
    
    for i in range(len(grid)):
        line = "┃" + (" " * spacing)
        for j in range(len(grid[i])):
            area = grid[i][j]
            # build a raw character (no color codes)
            if area[0] != 1:
                if area[0] == 2:
                    raw = "⚑"
                else:
                    raw = "#"
            elif area[0] == 2:
                raw = "⚑"
            else:
                # revealed
                if area[1] == 0:
                    # safe -> show count (if present)
                    cnt = area[2] if len(area) > 2 else 0
                    raw = " " if cnt == 0 else str(cnt)
                elif area[1] == 1:
                    raw = "✸"
                    

            # now decide coloring
            if player["pos"][0] == j and player["pos"][1] == i:
                # cursor highlight: black text on blue background for visibility
                char = Fore.BLACK + Back.BLUE + raw + Style.RESET_ALL
            else:
                # normal rendering: color numbers if >0, otherwise plain
                if raw.isdigit() and int(raw) > 0:
                    cnt = int(raw)
                    col = countcol[cnt] if cnt < len(countcol) else ""
                    char = col + raw + Style.RESET_ALL
                else:
                    char = raw

            line += char + (" " * spacing)
        line += "┃"
        centprint(line)
        for k in range(((spacing-1)//2)):
            print("┃" + (" " * (WIDTH*(1+spacing)+spacing)) + "┃")

    centprint("┗" + ("━" * (WIDTH*(1+spacing)+spacing)) + "┛")
    if not NotDead:
        centprint("BOOM!")
        
        NotDeadL = False
    

first = True  # still declared globally

def sweep():
    global NotDead, NotDeadL, first

    x = player["pos"][0]
    y = player["pos"][1]
    area = grid[y][x]

    if first:
        makemap(x, y)         # generate bombs excluding this area + neighbors
        first = False
        flood_fill(x, y)      # reveal initial region (includes the start cell)
        return                # first sweep handled

    # if flagged, do nothing
    if area[0] == 2:
        return

    # normal reveal
    area[0] = 1
    if area[1] == 1:
        NotDead = False

clear_and_home(True)
while NotDeadL:

    clear_and_home(False)
    
    main()
    
    event = keyboard.read_event()            # blocks until an event
    
    if event.event_type != "down":
        continue
    
    key = event.name

    if key == "left":
        player["pos"][0] = max(0, player["pos"][0]-1)
    elif key == "right":
        player["pos"][0] = min(gridsize[0]-1, player["pos"][0]+1)
    elif key == "up":
        player["pos"][1] = max(0, player["pos"][1]-1)
    elif key == "down":
        player["pos"][1] = min(gridsize[1]-1, player["pos"][1]+1)
    elif key == "z":
        sweep()
    elif key == "x":
        area = grid[player["pos"][1]][player["pos"][0]]
        if area[0] == 0:
            area[0] = 2
        elif area[0] == 2:
            area[0] = 0

os.system('pause >nul')
