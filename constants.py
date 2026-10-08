SCREEN_W, SCREEN_H = 1900, 1080
TILE_SIZE = 56
MAP_W, MAP_H = 40, 40
FPS = 60
PANEL_W   = 380
SIDEBAR_X = SCREEN_W - PANEL_W

# Colors
BLACK   = (0, 0, 0)
WHITE   = (255, 255, 255)
GRAY    = (128, 128, 128)
DGRAY   = (64, 64, 64)
RED     = (200, 50, 50)
GREEN   = (50, 200, 50)
BLUE    = (50, 100, 200)
YELLOW  = (220, 200, 50)
ORANGE  = (220, 130, 50)
PURPLE  = (150, 50, 200)
CYAN    = (50, 200, 200)
BROWN   = (139, 90, 43)
DGREEN  = (20, 100, 20)
DBLUE   = (20, 40, 120)

# Tile types
WALL  = 0
FLOOR = 1
DOOR  = 2
STAIRS_DOWN = 3
STAIRS_UP   = 4
WATER = 5
GRASS = 6
TRAP  = 7
CHASM = 8

TILE_COLORS = {
    WALL:        (60, 50, 40),
    FLOOR:       (100, 85, 70),
    DOOR:        (160, 110, 60),
    STAIRS_DOWN: (200, 200, 100),
    STAIRS_UP:   (200, 200, 100),
    WATER:       (40, 80, 160),
    GRASS:       (40, 120, 40),
    TRAP:        (100, 85, 70),
    CHASM:       (20, 20, 30),
}

TILE_CHARS = {
    WALL: '#', FLOOR: '.', DOOR: '+',
    STAIRS_DOWN: '>', STAIRS_UP: '<',
    WATER: '~', GRASS: ',', TRAP: '^', CHASM: ' ',
}

# Depth tiers
TIER = {1: (1,5), 2: (6,10), 3: (11,15), 4: (16,20), 5: (21,25)}

# Stats
BASE_HUNGER = 500
HUNGER_RATE = 1  # per turn

# Item types
WEAPON = 'weapon'
ARMOR  = 'armor'
POTION = 'potion'
SCROLL = 'scroll'
FOOD   = 'food'
WAND   = 'wand'
RING   = 'ring'
SEED   = 'seed'
GOLD   = 'gold'
MISSILE= 'missile'

# Directions
DIRS = {'up':(0,-1),'down':(0,1),'left':(-1,0),'right':(1,0),
        'ul':(-1,-1),'ur':(1,-1),'dl':(-1,1),'dr':(1,1)}

MAX_DEPTH = 25
BOSS_DEPTHS = {5, 10, 15, 20, 25}
