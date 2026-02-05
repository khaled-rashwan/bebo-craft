from PIL import Image

def create_atlas():
    # Load images
    try:
        top = Image.open('crafting_top.png').convert('RGBA')
        side = Image.open('crafting_side.png').convert('RGBA')
        bottom = Image.open('planks.png').convert('RGBA') # Use planks for bottom
    except FileNotFoundError as e:
        print(f"Error loading images: {e}")
        return

    # Resize to standard 16x16 if they aren't (just in case)
    top = top.resize((16, 16), Image.NEAREST)
    side = side.resize((16, 16), Image.NEAREST)
    bottom = bottom.resize((16, 16), Image.NEAREST)

    # Create new image 16x48 (stacked vertically)
    atlas = Image.new('RGBA', (16, 48))
    
    # Paste them: Top, Side, Bottom
    # Note: In Ursina/Panda3D UVs (0,0) is bottom-left. 
    # So if we map V 0.66-1.0 to top, that's the top of the image.
    atlas.paste(top, (0, 0))      # Top 1/3
    atlas.paste(side, (0, 16))    # Middle 1/3
    atlas.paste(bottom, (0, 32))  # Bottom 1/3

    atlas.save('crafting_table.png')
    print("Atlas 'crafting_table.png' created successfully.")

if __name__ == '__main__':
    create_atlas()
