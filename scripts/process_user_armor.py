from PIL import Image
import os

uploads = {
    'diamond_boots.png': r'C:/Users/asus/.gemini/antigravity/brain/ca9a594d-1477-467c-aa2d-530266052f45/uploaded_media_0_1770279757724.png',
    'diamond_leggings.png': r'C:/Users/asus/.gemini/antigravity/brain/ca9a594d-1477-467c-aa2d-530266052f45/uploaded_media_1_1770279757724.png',
    'diamond_chestplate.png': r'C:/Users/asus/.gemini/antigravity/brain/ca9a594d-1477-467c-aa2d-530266052f45/uploaded_media_2_1770279757724.png',
    'diamond_helmet.png': r'C:/Users/asus/.gemini/antigravity/brain/ca9a594d-1477-467c-aa2d-530266052f45/uploaded_media_3_1770279757724.png'
}

def process_image(src, dest):
    if not os.path.exists(src):
        print(f"File {src} not found!")
        return
    
    img = Image.open(src).convert("RGBA")
    datas = img.getdata()

    # Create new data with transparency
    # We will treat very light gray/white as transparent
    newData = []
    for item in datas:
        # Check if the pixel is white-ish or very light gray
        if item[0] > 240 and item[1] > 240 and item[2] > 240:
            newData.append((255, 255, 255, 0))
        else:
            newData.append(item)

    img.putdata(newData)
    img.save(dest)
    print(f"Processed and saved {dest}")

for dest, src in uploads.items():
    process_image(src, dest)
