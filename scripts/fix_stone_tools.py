from PIL import Image
import os

def process_stone_tool(filename, flip_needed=False):
    if not os.path.exists(filename):
        print(f"File {filename} not found.")
        return
        
    img = Image.open(filename).convert("RGBA")
    
    if flip_needed:
        # Some generated images might be upside down or mirrored
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
        img = img.transpose(Image.FLIP_TOP_BOTTOM)
    
    # Aggressive Transparency (anything close to white)
    datas = img.getdata()
    new_data = []
    for item in datas:
        # Check for white background (or near-white)
        # item is (R, G, B, A)
        if item[0] > 220 and item[1] > 220 and item[2] > 220:
            new_data.append((255, 255, 255, 0)) # Fully transparent
        else:
            new_data.append(item)

    img.putdata(new_data)
    img.save(filename)
    print(f"Processed {filename}.")

if __name__ == "__main__":
    # Stone sword usually needs to be diagonal. If it's horizontal/vertical, we might need rotation.
    # But for now let's just do transparency.
    process_stone_tool("stone_pickaxe.png")
    process_stone_tool("stone_axe.png")
    process_stone_tool("stone_shovel.png")
    process_stone_tool("stone_sword.png")
