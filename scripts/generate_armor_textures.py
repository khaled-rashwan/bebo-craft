from PIL import Image, ImageDraw

def create_texture(size, name, draw_func):
    img = Image.new('RGBA', size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    draw_func(draw, size)
    img.save(name)
    print(f"Created {name}")

def draw_helmet(draw, size):
    # Grey bucket shape
    draw.rectangle([4, 4, 11, 11], fill=(180, 180, 180, 255), outline=(100, 100, 100, 255))
    draw.rectangle([5, 8, 10, 9], fill=(50, 50, 50, 255)) # Visor slit

def draw_chestplate(draw, size):
    # Grey vest shape
    draw.rectangle([4, 4, 11, 11], fill=(180, 180, 180, 255), outline=(100, 100, 100, 255))
    draw.rectangle([2, 5, 4, 8], fill=(180, 180, 180, 255), outline=(100, 100, 100, 255)) # Left arm
    draw.rectangle([11, 5, 13, 8], fill=(180, 180, 180, 255), outline=(100, 100, 100, 255)) # Right arm

def draw_leggings(draw, size):
    # Grey pants shape
    draw.rectangle([4, 4, 11, 8], fill=(180, 180, 180, 255), outline=(100, 100, 100, 255))
    draw.rectangle([4, 8, 6, 13], fill=(180, 180, 180, 255), outline=(100, 100, 100, 255)) # Left leg
    draw.rectangle([9, 8, 11, 13], fill=(180, 180, 180, 255), outline=(100, 100, 100, 255)) # Right leg

def draw_boots(draw, size):
    # Grey boots
    draw.rectangle([3, 10, 6, 13], fill=(180, 180, 180, 255), outline=(100, 100, 100, 255)) # Left boot
    draw.rectangle([9, 10, 12, 13], fill=(180, 180, 180, 255), outline=(100, 100, 100, 255)) # Right boot

def draw_armor_icon(draw, size):
    # Shield shape
    points = [(8, 2), (13, 4), (13, 10), (8, 14), (3, 10), (3, 4)]
    draw.polygon(points, fill=(180, 180, 180, 255), outline=(100, 100, 100, 255))

create_texture((16, 16), 'iron_helmet.png', draw_helmet)
create_texture((16, 16), 'iron_chestplate.png', draw_chestplate)
create_texture((16, 16), 'iron_leggings.png', draw_leggings)
create_texture((16, 16), 'iron_boots.png', draw_boots)
create_texture((16, 16), 'armor_icon.png', draw_armor_icon)
