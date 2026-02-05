from PIL import Image, ImageDraw

def create_texture(size, name, pixels):
    img = Image.new('RGBA', size, (255, 255, 255, 0))
    for x, y, color in pixels:
        img.putpixel((x, y), color)
    # Scale up for better visibility in some viewers, but keep it 16x16 for game
    img.save(name)
    print(f"Created {name}")

# Shading colors
AQUA = (0, 255, 255, 255)
DARK_AQUA = (0, 180, 180, 255)
LIGHT_AQUA = (180, 255, 255, 255)
BLACK = (20, 20, 20, 255)
BROWN = (100, 60, 20, 255)
DARK_BROWN = (60, 30, 10, 255)

def get_diamond_pickaxe():
    pixels = []
    # Handle (Diagonal)
    for i in range(10):
        pixels.append((2+i, 13-i, BROWN))
        if i < 9: pixels.append((2+i+1, 13-i, BLACK)) # outline
    
    # Pickaxe Head (Classic curve)
    head_pts = [
        (2,2), (3,2), (4,2), (5,2), (6,2), (7,2), (8,2), (9,2), (10,2), (11,2), (12,2), (13,2),
        (3,3), (4,3), (5,3), (10,3), (11,3), (12,3),
        (4,4), (11,4)
    ]
    for x, y in head_pts:
        pixels.append((x, y, AQUA))
        # Add some shading
        if x < 7: pixels.append((x, y, LIGHT_AQUA))
        elif x > 8: pixels.append((x, y, DARK_AQUA))
    
    # Handle shading/outline
    pixels.append((7, 7, DARK_BROWN))
    pixels.append((8, 6, DARK_BROWN))
    
    return pixels

def get_diamond_sword():
    pixels = []
    # Blade
    for i in range(10):
        pixels.append((3+i, 12-i, AQUA))
        pixels.append((3+i+1, 12-i, AQUA))
        pixels.append((3+i, 12-i-1, AQUA))
        # Highlight
        pixels.append((3+i, 12-i, LIGHT_AQUA))
        # Outline
        pixels.append((3+i-1, 12-i, BLACK))
        pixels.append((3+i, 12-i+1, BLACK))

    # Guard
    pixels.append((2, 11, BLACK))
    pixels.append((3, 11, DARK_AQUA))
    pixels.append((4, 11, BLACK))
    pixels.append((11, 4, BLACK))
    pixels.append((11, 3, DARK_AQUA))
    pixels.append((11, 2, BLACK))
    
    # Handle
    pixels.append((1, 14, BLACK))
    pixels.append((2, 14, BROWN))
    pixels.append((2, 13, BROWN))
    pixels.append((3, 12, BLACK))
    
    return pixels

def get_diamond_axe():
    pixels = []
    # Handle
    for i in range(11):
        pixels.append((4+i, 14-i, BROWN))
    # Head
    for x in range(2, 7):
        for y in range(2, 7):
            pixels.append((x, y, AQUA))
    pixels.append((3, 7, AQUA))
    pixels.append((7, 3, AQUA))
    
    return pixels

def get_diamond_shovel():
    pixels = []
    # Handle
    for i in range(11):
        pixels.append((2+i, 13-i, BROWN))
    # Head
    pixels.append((11, 2, AQUA))
    pixels.append((12, 2, AQUA))
    pixels.append((13, 2, AQUA))
    pixels.append((11, 3, AQUA))
    pixels.append((12, 3, AQUA))
    pixels.append((13, 3, AQUA))
    pixels.append((11, 4, AQUA))
    pixels.append((12, 4, AQUA))
    pixels.append((13, 4, AQUA))
    
    return pixels

create_texture((16, 16), 'diamond_pickaxe.png', get_diamond_pickaxe())
create_texture((16, 16), 'diamond_sword.png', get_diamond_sword())
create_texture((16, 16), 'diamond_axe.png', get_diamond_axe())
create_texture((16, 16), 'diamond_shovel.png', get_diamond_shovel())
