from PIL import Image
import os

def flip_and_clean(filename):
    if not os.path.exists(filename):
        print(f"File {filename} not found.")
        return
        
    img = Image.open(filename).convert("RGBA")
    
    # Flip both ways to match the sword/pickaxe orientation (bottom-left handle)
    img = img.transpose(Image.FLIP_LEFT_RIGHT)
    img = img.transpose(Image.FLIP_TOP_BOTTOM)
    
    # Transparency
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
    print(f"Flipped and cleaned {filename}.")

if __name__ == "__main__":
    flip_and_clean("wood_shovel.png")
