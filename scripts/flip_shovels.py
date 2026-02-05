from PIL import Image
import os

def flip_vertical(filename):
    if not os.path.exists(filename):
        print(f"File {filename} not found.")
        return
        
    img = Image.open(filename).convert("RGBA")
    # Flip top to bottom
    flipped_img = img.transpose(Image.FLIP_TOP_BOTTOM)
    # Also rotate 180 if needed, but FLIP_TOP_BOTTOM should do what user wants (stone up, handle down)
    flipped_img.save(filename)
    print(f"Flipped {filename} vertically.")

if __name__ == "__main__":
    flip_vertical("stone_shovel.png")
    flip_vertical("wood_shovel.png")
