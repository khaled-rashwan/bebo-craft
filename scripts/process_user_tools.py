from PIL import Image
import os

uploads = {
    'diamond_pickaxe.png': r'C:/Users/asus/.gemini/antigravity/brain/ca9a594d-1477-467c-aa2d-530266052f45/uploaded_media_0_1770279405285.png',
    'diamond_sword.png': r'C:/Users/asus/.gemini/antigravity/brain/ca9a594d-1477-467c-aa2d-530266052f45/uploaded_media_1_1770279405285.png',
    'diamond_axe.png': r'C:/Users/asus/.gemini/antigravity/brain/ca9a594d-1477-467c-aa2d-530266052f45/uploaded_media_2_1770279405285.png',
    'diamond_shovel.png': r'C:/Users/asus/.gemini/antigravity/brain/ca9a594d-1477-467c-aa2d-530266052f45/uploaded_media_3_1770279405285.png'
}

def process_image(src, dest):
    if not os.path.exists(src):
        print(f"File {src} not found!")
        return
    
    img = Image.open(src).convert("RGBA")
    datas = img.getdata()

    # Get background color from top-left pixel
    bg_color = img.getpixel((0, 0))
    
    newData = []
    for item in datas:
        # If the pixel is close to the background color, make it transparent
        # Using a small threshold for fuzzy backgrounds
        if abs(item[0] - bg_color[0]) < 10 and abs(item[1] - bg_color[1]) < 10 and abs(item[2] - bg_color[2]) < 10:
            newData.append((255, 255, 255, 0))
        else:
            newData.append(item)

    img.putdata(newData)
    # Ensure it's square/clean for Ursina if needed, but original is fine
    img.save(dest)
    print(f"Processed and saved {dest}")

for dest, src in uploads.items():
    process_image(src, dest)
