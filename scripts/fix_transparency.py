from PIL import Image
import os

def make_transparent(filename):
    if not os.path.exists(filename):
        print(f"File {filename} not found.")
        return
        
    img = Image.open(filename).convert("RGBA")
    datas = img.getdata()

    new_data = []
    for item in datas:
        # Check for white background (or near-white)
        if item[0] > 240 and item[1] > 240 and item[2] > 240:
            new_data.append((255, 255, 255, 0)) # Fully transparent
        else:
            new_data.append(item)

    img.putdata(new_data)
    img.save(filename)
    print(f"Made {filename} transparent.")

if __name__ == "__main__":
    make_transparent("stick.png")
    make_transparent("wood_pickaxe.png")
    make_transparent("wood_sword.png")
    make_transparent("wood_shovel.png")
    make_transparent("zombie.png")
    make_transparent("wood_axe.png")
    make_transparent("stone_pickaxe.png")
    make_transparent("stone_axe.png")
    make_transparent("stone_shovel.png")
    make_transparent("stone_sword.png")
