from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import random
import math
import json
import os

app = Ursina()
window.title = 'BeboCraft'
window.icon = 'textures/logo.ico'
player = FirstPersonController(position=(10, 6, 10), mouse_sensitivity=(100, 100))
player.enabled = False # Start disabled for menu

# Environment
sky = Sky()
sun = DirectionalLight(y=10, rotation=(45, 45, 45))
sun.shadow_map_res = 1024

# Held Item (First Person Hand/Tool)
held_item = Entity(
    parent=camera,
    model='cube',
    texture='hand.png',
    scale=(0.2, 0.3, 0.2),
    position=(0.6, -0.4, 0.8),
    rotation=(10, -20, 10),
    shader=None
)

# Health system
health = 10
user_spawn_point = (10, 6, 10)
hearts = []
for i in range(health):
    heart = Entity(
        model='quad',
        texture='heart.png',
        parent=camera.ui,
        scale=(0.05, 0.05),
        position=(-0.85 + (i * 0.06), -0.45)
    )
    hearts.append(heart)

# Armor system
armor_points = 0
armor_icons = []
for i in range(10): # 10 icons for 20 points max (like hearts)
    icon = Entity(
        model='quad',
        texture='armor_icon.png',
        parent=camera.ui,
        scale=(0.05, 0.05),
        position=(-0.85 + (i * 0.06), -0.38),
        enabled=False
    )
    armor_icons.append(icon)

equipped_armor = {'helmet': None, 'chestplate': None, 'leggings': None, 'boots': None}
armor_values = {
    'iron_helmet.png': 2,
    'iron_chestplate.png': 6,
    'iron_leggings.png': 5,
    'iron_boots.png': 2,
    'diamond_helmet.png': 3,
    'diamond_chestplate.png': 8,
    'diamond_leggings.png': 6,
    'diamond_boots.png': 3
}

# Crosshair
crosshair = Text(parent=camera.ui, text='+', position=(0,0), origin=(0,0), scale=2)

# Block Selector (Highlight)
selector = Entity(model='cube', color=color.rgba(255,255,255,0.4), scale=1.01, origin_y=-0.5)
selector.enabled = False

# Particles for breaking blocks
class Particle(Entity):
    def __init__(self, position, texture):
        super().__init__(
            model='cube',
            texture=texture,
            position=position,
            scale=random.uniform(0.05, 0.15),
            color=color.white
        )
        self.velocity = Vec3(
            random.uniform(-0.1, 0.1),
            random.uniform(0.1, 0.3),
            random.uniform(-0.1, 0.1)
        ) * 40
        self.gravity = 0.8
        self.lifetime = 1.0

    def update(self):
        self.velocity.y -= self.gravity
        self.position += self.velocity * time.dt
        self.lifetime -= time.dt
        self.scale *= 0.95 # Shrink
        if self.lifetime <= 0:
            destroy(self)

# Zombie Mob
class Zombie(Entity):
    def __init__(self, **kwargs):
        super().__init__(
            model='cube',
            texture='zombie.png',
            scale=(1, 2, 1),
            origin_y=-0.5,
            collider='box',
            **kwargs
        )
        self.health = 10
        self.speed = 3

    def update(self):
        # Look at player (but keep Y level)
        target_pos = Vec3(player.x, self.y, player.z)
        self.look_at(target_pos)
        self.rotation_x = 0 # Keep upright
        
        # Move toward player
        dist = distance_xz(self.position, player.position)
        if dist > 1.2:
            self.position += self.forward * self.speed * time.dt
        else:
            # Attack player
            if not hasattr(self, 'attack_timer'): self.attack_timer = 0
            self.attack_timer += time.dt
            if self.attack_timer >= 1.0: # Attack every 1 second
                take_damage(1) # 1 base heart damage
                self.attack_timer = 0
            
        # Grounding
        self.y = 0 # Simple grounding to floor y=0 (or whatever ground level is)
        # In a real voxel world we'd use raycast or check world.voxels but y=1 (top of block) is safer
        self.y = 1

    def hit(self, damage):
        self.health -= damage
        # Hit feedback (red particles)
        for _ in range(5):
             p = Particle(position=self.position + Vec3(0, 1, 0), texture='heart.png') # Use heart as red part
             p.color = color.red
             p.scale = 0.05
             
        if self.health <= 0:
            # Death particles
            for _ in range(15):
                p = Particle(position=self.position + Vec3(0, 1, 0), texture='zombie.png')
                p.scale = random.uniform(0.1, 0.2)
            destroy(self)

# Spawning state
current_wave = 0
night_spawn_active = False

# Block Breaking State
breaking_pos = None
breaking_timer = 0
is_breaking = False
breaking_duration = 3.0

# Crack Overlay (Visual Cracking Effect)
crack_overlay = Entity(
    model='cube',
    texture='crack.png',
    scale=1.02,
    render_queue=1,
    texture_scale=(0.5, 0.5), # 2x2 spritesheet
    color=color.white, # No tinting
    enabled=False
)
# Crack levels (offset x, offset y)
crack_offsets = [(0, 0.5), (0.5, 0.5), (0, 0), (0.5, 0)]

last_held_tex = None

# Inventory system
# Inventory Data (0-4: Hotbar, 5-29: Main Inventory)
inventory = [{'texture': 'grass.png', 'count': 64}, {'texture': 'spawn_point.png', 'count': 64}] + [None] * 28
selected_slot = 0
inventory_slots = []
inventory_icons = []
inventory_texts = []

# Full Inventory Panel
inventory_panel = Entity(parent=camera.ui, model='quad', scale=(0.5, 0.5), color=color.black66, enabled=False)
full_slots = []
full_icons = []
full_texts = []

for i in range(5):
    slot = Entity(
        model='quad',
        parent=camera.ui,
        scale=(0.08, 0.08),
        position=(-0.16 + (i * 0.09), -0.4),
        color=color.black66,
        collider='box'
    )
    inventory_slots.append(slot)
    
    icon = Entity(
        model='quad',
        parent=slot,
        scale=(0.8, 0.8),
        position=(0, 0, -1),
        texture=inventory[i]['texture'] if inventory[i] else None,
        enabled=True if inventory[i] else False
    )
    inventory_icons.append(icon)
    
    txt = Text(
        text='',
        parent=slot,
        scale=12,
        position=(0.2, -0.2, -2),
        origin=(0, 0),
        color=color.white
    )
    inventory_texts.append(txt)

# Global input for block interaction
# Global input for block interaction
# Interaction State
is_table_open = False
game_state = 'MENU' # MENU, PLAYING, PAUSED
current_world_name = "NewWorld"
world_name_text = Text(text="", parent=camera.ui, position=(0.88, 0.48), origin=(0.5, 0.5), scale=1, color=color.yellow, enabled=False)

camera_mode = 0 # 0: 1st, 1: 3rd Back, 2: 3rd Front
player_model = Entity(parent=player, model='cube', texture='zombie.png', scale=(0.8, 1.8, 0.5), origin_y=-0.5, enabled=False)
# Adjust player model position slightly so it doesn't clip with the camera in 1st person
player_model.y = 0 

# Item Properties
NON_BLOCKS = ['stick.png', 'wood_pickaxe.png', 'wood_sword.png', 'wood_shovel.png', 'wood_axe.png',
              'stone_pickaxe.png', 'stone_sword.png', 'stone_shovel.png', 'stone_axe.png', 
              'iron_ingot.png', 'iron_pickaxe.png', 'iron_axe.png', 'iron_sword.png', 'iron_shovel.png', 'diamond.png',
              'iron_helmet.png', 'iron_chestplate.png', 'iron_leggings.png', 'iron_boots.png',
              'diamond_pickaxe.png', 'diamond_axe.png', 'diamond_sword.png', 'diamond_shovel.png',
              'diamond_helmet.png', 'diamond_chestplate.png', 'diamond_leggings.png', 'diamond_boots.png']
STACK_LIMITS = {
    'wood_pickaxe.png': 1, 'wood_sword.png': 1, 'wood_shovel.png': 1, 'wood_axe.png': 1,
    'stone_pickaxe.png': 1, 'stone_sword.png': 1, 'stone_shovel.png': 1, 'stone_axe.png': 1,
    'iron_ore.png': 64, 'iron_ingot.png': 64, 'iron_pickaxe.png': 1, 'iron_axe.png': 1,
    'iron_sword.png': 1, 'iron_shovel.png': 1, 'diamond_ore.png': 64, 'diamond.png': 64,
    'iron_helmet.png': 1, 'iron_chestplate.png': 1, 'iron_leggings.png': 1, 'iron_boots.png': 1,
    'diamond_pickaxe.png': 1, 'diamond_axe.png': 1, 'diamond_sword.png': 1, 'diamond_shovel.png': 1,
    'diamond_helmet.png': 1, 'diamond_chestplate.png': 1, 'diamond_leggings.png': 1, 'diamond_boots.png': 1,
    'spawn_point.png': 64
}

def get_max_stack(texture):
    return STACK_LIMITS.get(texture, 64)

def swing():
    # Store original resting state (these are relative to parent camera)
    is_item = False
    item = inventory[selected_slot]
    if item and item['texture'] in NON_BLOCKS:
        is_item = True
    
    # Strike Forward: Tilt forward (Positive X) and move down/front
    target_pos = Vec3(0.5, -0.5, 1.0)
    target_rot = Vec3(50, -10, 10)
    
    # resting state
    rest_pos = Vec3(0.6, -0.4, 0.8)
    rest_rot = Vec3(10, -20, 10) if not is_item else Vec3(10, -20, 0)

    # Animation
    held_item.animate_position(target_pos, duration=0.1)
    held_item.animate_rotation(target_rot, duration=0.1)
    
    # Return
    invoke(held_item.animate_position, rest_pos, duration=0.1, delay=0.12)
    invoke(held_item.animate_rotation, rest_rot, duration=0.1, delay=0.12)

def input(key):
    global selected_slot, is_table_open
    
    if key == 'e' or key == 'c':
        if inventory_panel.enabled:
            is_table_open = False # Reset on close
        
        inventory_panel.enabled = not inventory_panel.enabled
        mouse.locked = not inventory_panel.enabled
        player.enabled = not inventory_panel.enabled
        if inventory_panel.enabled:
            update_inventory_ui()

    if key == 'escape' and game_state == 'PLAYING':
        toggle_pause()
        return

    if key == 'f5':
        global camera_mode
        camera_mode = (camera_mode + 1) % 3
        
        if camera_mode == 0: # 1st Person
            camera.z = 0
            camera.rotation_y = 0
            player_model.enabled = False
            held_item.enabled = True
        elif camera_mode == 1: # 3rd Person Back
            camera.z = -10
            camera.rotation_y = 0
            player_model.enabled = True
            held_item.enabled = False
        elif camera_mode == 2: # 3rd Person Front
            camera.z = 10
            camera.rotation_y = 180
            player_model.enabled = True
            held_item.enabled = False
            
    # Inventory Interaction (Drag & Drop)
    if (key == 'left mouse down' or key == 'right mouse down') and inventory_panel.enabled:
        hovered = mouse.hovered_entity
        global cursor_item
        
        # Helper to handle clicking a slot
        def handle_slot_click(slot_type, index):
            global cursor_item
            
            # Get item from correct list
            current_item = None
            if slot_type == 'inventory': current_item = inventory[index]
            elif slot_type == 'crafting': current_item = crafting_grid[index]
            elif slot_type == 'output': current_item = crafting_result
            
            if key == 'right mouse down':
                # Right Click Logic (Place One)
                if cursor_item:
                    if slot_type == 'output':
                        # Output handles same as left click for simplicity (craft all/stack)
                        # Or we could just ignore right click on output to avoid confusion
                        pass 
                    else:
                        if current_item is None:
                            # Place 1 into empty slot
                            new_item = cursor_item.copy()
                            new_item['count'] = 1
                            if slot_type == 'inventory': inventory[index] = new_item
                            elif slot_type == 'crafting': crafting_grid[index] = new_item
                            
                            cursor_item['count'] -= 1
                            if cursor_item['count'] <= 0: cursor_item = None
                        
                        elif current_item['texture'] == cursor_item['texture'] and current_item['count'] < get_max_stack(current_item['texture']):
                            # Add 1 to existing stack
                            current_item['count'] += 1
                            cursor_item['count'] -= 1
                            if cursor_item['count'] <= 0: cursor_item = None
                else:
                    # Right click empty/filled slot with empty cursor -> Equip Armor?
                    if current_item and slot_type == 'inventory':
                        tex = current_item['texture']
                        piece = None
                        if 'helmet' in tex: piece = 'helmet'
                        elif 'chestplate' in tex: piece = 'chestplate'
                        elif 'leggings' in tex: piece = 'leggings'
                        elif 'boots' in tex: piece = 'boots'
                        
                        if piece:
                            old_armor = equipped_armor[piece]
                            equipped_armor[piece] = current_item
                            inventory[index] = old_armor # Swap back
                            update_inventory_ui()
                            update_armor_ui()
                            return

            else:
                # Left Click Logic (Standard)
                if cursor_item is None:
                    # Pick up
                    if current_item:
                        if slot_type == 'output':
                            # Crafting logic: Consume ingredients
                                cursor_item = current_item.copy()
                                for i in range(9):
                                    if crafting_grid[i]:
                                        crafting_grid[i]['count'] -= 1
                                        if crafting_grid[i]['count'] <= 0:
                                            crafting_grid[i] = None
                                check_recipes()
                        else:
                            cursor_item = current_item
                            if slot_type == 'inventory': inventory[index] = None
                            elif slot_type == 'crafting': crafting_grid[index] = None
                                
                else:
                    # Place / Swap / Stack
                    if slot_type == 'output':
                        # Can only take from output if cursor matches and stackable
                        max_s = get_max_stack(cursor_item['texture'])
                        if current_item and cursor_item['texture'] == current_item['texture'] and cursor_item['count'] + current_item['count'] <= max_s:
                                cursor_item['count'] += current_item['count']
                                for i in range(4):
                                    if crafting_grid[i]:
                                        crafting_grid[i]['count'] -= 1
                                        if crafting_grid[i]['count'] <= 0:
                                            crafting_grid[i] = None
                                check_recipes()
                    else:
                        # Standard slot
                        if current_item is None:
                            # Place All
                            if slot_type == 'inventory': inventory[index] = cursor_item
                            elif slot_type == 'crafting': crafting_grid[index] = cursor_item
                            cursor_item = None
                        else:
                            # Stack or Swap
                            if current_item['texture'] == cursor_item['texture']:
                                # Stack
                                max_s = get_max_stack(current_item['texture'])
                                space = max_s - current_item['count']
                                to_add = min(space, cursor_item['count'])
                                current_item['count'] += to_add
                                cursor_item['count'] -= to_add
                                if cursor_item['count'] <= 0: cursor_item = None
                            else:
                                # Swap
                                temp = current_item
                                if slot_type == 'inventory': inventory[index] = cursor_item
                                elif slot_type == 'crafting': crafting_grid[index] = cursor_item
                                cursor_item = temp
            
            if slot_type == 'crafting': check_recipes()
            update_inventory_ui()


        # Detect which slot was clicked
        if hovered in inventory_slots:
            handle_slot_click('inventory', inventory_slots.index(hovered))
        elif hovered in full_slots:
            handle_slot_click('inventory', full_slots.index(hovered) + 5)
        elif hovered in crafting_slots:
            handle_slot_click('crafting', crafting_slots.index(hovered))
        elif hovered == output_slot or hovered == output_icon:
                handle_slot_click('output', 0)


    if player.enabled:
        global is_breaking, breaking_pos, breaking_timer
        
        # Left Click: Start Breaking Block
        if key == 'left mouse down':
            swing()
            
            # Check for Zombie hit first
            if mouse.hovered_entity and isinstance(mouse.hovered_entity, Zombie):
                damage = 1.0 # Default
                item = inventory[selected_slot]
                if item:
                    if item['texture'] == 'wood_sword.png':
                        damage = 1.45 # 7 hits
                    elif item['texture'] == 'stone_sword.png':
                        damage = 2.5  # 10 HP / 4 hits = 2.5
                    elif item['texture'] == 'iron_sword.png':
                        damage = 3.4  # 10 HP / 3 hits = 3.33...
                    elif item['texture'] == 'diamond_sword.png':
                        damage = 5.0  # 10 HP / 2 hits
                
                mouse.hovered_entity.hit(damage)
                return

            hit_info = raycast(camera.world_position, camera.forward, distance=5)
            if hit_info.hit:
                pos = hit_info.world_point - hit_info.normal * 0.5
                pos = (math.floor(pos[0]), math.floor(pos[1]), math.floor(pos[2]))
                
                if world.voxels_get(pos):
                    is_breaking = True
                    breaking_pos = pos
                    breaking_timer = 0
                    
                    # Position crack overlay
                    crack_overlay.enable()
                    crack_overlay.position = Vec3(breaking_pos) + Vec3(0, 0.51, 0)
        
        if key == 'left mouse up':
            is_breaking = False
            crack_overlay.disable()
            breaking_timer = 0
            
        # Right Click: Place / Interact
        if key == 'right mouse down':
            # Check for Armor Equip in Hotbar
            item = inventory[selected_slot]
            if item:
                tex = item['texture']
                piece = None
                if 'helmet' in tex: piece = 'helmet'
                elif 'chestplate' in tex: piece = 'chestplate'
                elif 'leggings' in tex: piece = 'leggings'
                elif 'boots' in tex: piece = 'boots'
                
                if piece:
                    old_armor = equipped_armor[piece]
                    equipped_armor[piece] = item
                    inventory[selected_slot] = old_armor # Swap back to hotbar
                    update_inventory_ui()
                    update_armor_ui()
                    # Play a sound or swing?
                    swing()
                    return

            hit_info = raycast(camera.world_position, camera.forward, distance=5)
            if hit_info.hit:
                # Check for Interaction (Crafting Table)
                hit_block_pos = hit_info.world_point - hit_info.normal * 0.5
                hit_block_pos = (math.floor(hit_block_pos[0]), math.floor(hit_block_pos[1]), math.floor(hit_block_pos[2]))
                
                block_tex = world.voxels_get(hit_block_pos)
                if block_tex == 'crafting_table.png':
                    # Open Crafting UI (3x3 Mode)
                    is_table_open = True
                    inventory_panel.enabled = True
                    mouse.locked = False
                    player.enabled = False
                    update_inventory_ui()
                    return 

                # Place Block logic
                if inventory[selected_slot]:
                    # Prevent placing non-blocks
                    if inventory[selected_slot]['texture'] in NON_BLOCKS:
                        return

                    # Find position for new block
                    new_pos = hit_info.world_point + hit_info.normal * 0.5
                    new_pos = (math.floor(new_pos[0]), math.floor(new_pos[1]), math.floor(new_pos[2]))
                    
                    tex = inventory[selected_slot]['texture']
                    world.add_block(new_pos, tex)
                    
                    if tex == 'spawn_point.png':
                        global user_spawn_point
                        user_spawn_point = (new_pos[0], new_pos[1] + 1, new_pos[2])
                    
                    inventory[selected_slot]['count'] -= 1
                    if inventory[selected_slot]['count'] <= 0:
                        inventory[selected_slot] = None
                    update_inventory_ui()

# Create Full Inventory Grid (5x5)
for y in range(5):
    for x in range(5):
        i = 5 + (y * 5) + x
        slot = Entity(
            model='quad',
            parent=inventory_panel,
            scale=(0.15, 0.15),
            position=(-0.36 + (x * 0.18), 0.36 - (y * 0.18)),
            color=color.black,
            collider='box'
        )
        full_slots.append(slot)
        
        icon = Entity(
            model='quad',
            parent=slot,
            scale=(0.8, 0.8),
            position=(0, 0, -1),
            enabled=False
        )
        full_icons.append(icon)
        
        txt = Text(
            text='',
            parent=slot,
            scale=12,
            position=(0.2, -0.2, -2),
            origin=(0, 0),
            color=color.white
        )
        full_texts.append(txt)

def update_inventory_ui():
    for i in range(5):
        # Update hotbar
        if inventory[i]:
            inventory_icons[i].texture = inventory[i]['texture']
            inventory_icons[i].enabled = True
            inventory_texts[i].text = str(inventory[i]['count']) if inventory[i]['count'] > 1 else ''
        else:
            inventory_icons[i].enabled = False
            inventory_texts[i].text = ''
        
        # Update highlight
        if i == selected_slot:
            inventory_slots[i].color = color.white
            inventory_slots[i].scale = (0.09, 0.09)
        else:
            inventory_slots[i].color = color.black66
            inventory_slots[i].scale = (0.08, 0.08)
            
    # Update full inventory panel
    for i in range(25):
        inv_idx = i
        if inv_idx >= 5: # Indices 5-24 are in the full panel
            full_idx = inv_idx - 5
            if inventory[inv_idx]:
                full_icons[full_idx].texture = inventory[inv_idx]['texture']
                full_icons[full_idx].enabled = True
                full_texts[full_idx].text = str(inventory[inv_idx]['count']) if inventory[inv_idx]['count'] > 1 else ''
            else:
                full_icons[full_idx].enabled = False
                full_texts[full_idx].text = ''

    # Update Crafting UI
    for i in range(9):
        # Determine visibility based on mode
        # 3x3 uses all 9. 2x2 uses index 0,1,3,4 (top-left square)
        is_visible = False
        if is_table_open:
            is_visible = True
        else:
            if i in [0, 1, 3, 4]:
                is_visible = True
        
        crafting_slots[i].enabled = is_visible
        
        # Position adjustments for 2x2 mode
        if not is_table_open:
            # Shift 2x2 grid slightly so it looks centered
            row = i // 3
            col = i % 3
            if is_visible:
                crafting_slots[i].position = (0.55 + (col * 0.18), 0.2 - (row * 0.18))
        else:
            # Standard 3x3 positions
            row = i // 3
            col = i % 3
            crafting_slots[i].position = (0.45 + (col * 0.18), 0.28 - (row * 0.18))

        if crafting_grid[i] and is_visible:
            crafting_icons[i].texture = crafting_grid[i]['texture']
            crafting_icons[i].enabled = True
        else:
            crafting_icons[i].enabled = False
            
    if is_table_open:
        output_slot.position = (1.1, 0.11)
        arrow.position = (0.95, 0.11)
    else:
        output_slot.position = (1.05, 0.11)
        arrow.position = (0.9, 0.11)

    if crafting_result:
        output_icon.texture = crafting_result['texture']
        output_icon.enabled = True
        output_text.text = str(crafting_result['count'])
    else:
        output_icon.enabled = False
        output_text.text = ''

# Crafting System
crafting_grid = [None] * 9
crafting_result = None
crafting_slots = []
crafting_icons = []

# Crafting UI (3x3 Grid)
for y in range(3):
    for x in range(3):
        i = y * 3 + x
        slot = Entity(
            model='quad',
            parent=inventory_panel,
            scale=(0.15, 0.15),
            position=(0.45 + (x * 0.18), 0.28 - (y * 0.18)),
            color=color.black66,
            collider='box'
        )
        crafting_slots.append(slot)
        
        icon = Entity(
            model='quad',
            parent=slot,
            scale=(0.8, 0.8),
            position=(0, 0, -1),
            enabled=False
        )
        crafting_icons.append(icon)

# Crafting Output
output_slot = Entity(
    model='quad',
    parent=inventory_panel,
    scale=(0.15, 0.15),
    position=(1.1, 0.11),
    color=color.black66,
    collider='box'
)
output_icon = Entity(
    model='quad',
    parent=output_slot,
    scale=(0.8, 0.8),
    position=(0, 0, -1),
    enabled=False
)
output_text = Text(
    text='',
    parent=output_slot,
    scale=12,
    position=(0.2, -0.2, -2),
    origin=(0, 0),
    color=color.white
)

arrow = Text(
    text='->',
    parent=inventory_panel,
    position=(0.95, 0.11),
    scale=2,
    origin=(0,0)
)

# Cursor Item (Drag & Drop)
cursor_item = None
cursor_icon = Entity(parent=camera.ui, model='quad', scale=0.07, z=-10, enabled=False)

def check_recipes():
    global crafting_result
    # Simple Recipe: 1 Wood -> 4 Stone (Planks placeholder)
    # Recipe Logic
    wood_count = 0
    planks_count = 0
    stone_count = 0
    iron_ingot_count = 0
    diamond_count = 0
    other_count = 0
    
    for item in crafting_grid:
        if item:
            tex = item['texture']
            if tex == 'wood.png':
                wood_count += 1
            elif tex == 'planks.png':
                planks_count += 1
            elif tex == 'stone.png':
                stone_count += 1
            elif tex == 'iron_ingot.png':
                iron_ingot_count += 1
            elif tex == 'diamond.png':
                diamond_count += 1
            else:
                other_count += 1
    
    # 1 Wood -> 4 Planks
    if wood_count == 1 and planks_count == 0 and other_count == 0:
        crafting_result = {'texture': 'planks.png', 'count': 4}
    # 4 Planks -> 1 Crafting Table
    elif planks_count == 4 and wood_count == 0 and other_count == 0:
        crafting_result = {'texture': 'crafting_table.png', 'count': 1}
    # 2 Vertical Planks -> 4 Sticks
    elif planks_count == 2 and wood_count == 0 and other_count == 0:
        # Check specifically for vertical alignment
        is_vertical = False
        for i in range(6): # Check pairs (0,3), (1,4), (2,5), (3,6), (4,7), (5,8)
            if crafting_grid[i] and crafting_grid[i+3]:
                if crafting_grid[i]['texture'] == 'planks.png' and crafting_grid[i+3]['texture'] == 'planks.png':
                    is_vertical = True
                    break
        if is_vertical:
            crafting_result = {'texture': 'stick.png', 'count': 4}
        else:
            crafting_result = None
    # Tools with 3 Planks + 2 Sticks (Pickaxe or Axe)
    elif planks_count == 3 and other_count == 2:
        c = crafting_grid
        # Wooden Pickaxe (3 Planks row, 2 Sticks center)
        if (c[0] and c[1] and c[2] and c[4] and c[7] and
            c[0]['texture'] == 'planks.png' and c[1]['texture'] == 'planks.png' and c[2]['texture'] == 'planks.png' and
            c[4]['texture'] == 'stick.png' and c[7]['texture'] == 'stick.png'):
            crafting_result = {'texture': 'wood_pickaxe.png', 'count': 1}
        # Wooden Axe Pattern 1: [0,1,3] planks, [4,7] sticks
        elif (c[0] and c[1] and c[3] and c[4] and c[7] and
            c[0]['texture'] == 'planks.png' and c[1]['texture'] == 'planks.png' and
            c[3]['texture'] == 'planks.png' and
            c[4]['texture'] == 'stick.png' and c[7]['texture'] == 'stick.png'):
            crafting_result = {'texture': 'wood_axe.png', 'count': 1}
        # Wooden Axe Pattern 2 (Mirrored): [1,2,5] planks, [4,7] sticks
        elif (c[1] and c[2] and c[5] and c[4] and c[7] and
            c[1]['texture'] == 'planks.png' and c[2]['texture'] == 'planks.png' and
            c[5]['texture'] == 'planks.png' and
            c[4]['texture'] == 'stick.png' and c[7]['texture'] == 'stick.png'):
            crafting_result = {'texture': 'wood_axe.png', 'count': 1}
        else:
            crafting_result = None
    # Wooden Sword (2 Planks vertical, 1 Stick bottom)
    elif planks_count == 2 and other_count == 1:
        # middle column check: 1, 4, 7
        if (crafting_grid[1] and crafting_grid[4] and crafting_grid[7]):
            c = crafting_grid
            if (c[1]['texture'] == 'planks.png' and c[4]['texture'] == 'planks.png' and
                c[7]['texture'] == 'stick.png'):
                crafting_result = {'texture': 'wood_sword.png', 'count': 1}
            else:
                crafting_result = None
        else:
            crafting_result = None
    # Wooden Shovel (1 Plank top, 2 Sticks vertical below)
    elif planks_count == 1 and other_count == 2:
        # middle column check: 1, 4, 7
        if (crafting_grid[1] and crafting_grid[4] and crafting_grid[7]):
            c = crafting_grid
            if (c[1]['texture'] == 'planks.png' and c[4]['texture'] == 'stick.png' and
                c[7]['texture'] == 'stick.png'):
                crafting_result = {'texture': 'wood_shovel.png', 'count': 1}
            else:
                crafting_result = None
        else:
            crafting_result = None

    # --- STONE TOOLS (Stone + Sticks) ---
    # Stone Pickaxe (3 Stone top row + 2 Sticks center column)
    elif stone_count == 3 and other_count == 2:
        c = crafting_grid
        # Check all 3 columns for T-shape and Axe patterns
        found = False
        # T-shape (Pickaxe)
        for i in [1]: # Usually pickaxe is centered, but we can allow 0 and 2 if we had more room. 
                      # For pickaxe, let's just stick to slot 1 for the vertical stick part.
            if (c[0] and c[1] and c[2] and c[4] and c[7] and
                c[0]['texture'] == 'stone.png' and c[1]['texture'] == 'stone.png' and c[2]['texture'] == 'stone.png' and
                c[4]['texture'] == 'stick.png' and c[7]['texture'] == 'stick.png'):
                crafting_result = {'texture': 'stone_pickaxe.png', 'count': 1}
                found = True
                break
        
        if not found:
            # Stone Axe Pattern 1 (Left-facing)
            if (c[0] and c[1] and c[3] and c[4] and c[7] and
                c[0]['texture'] == 'stone.png' and c[1]['texture'] == 'stone.png' and c[3]['texture'] == 'stone.png' and
                c[4]['texture'] == 'stick.png' and c[7]['texture'] == 'stick.png'):
                crafting_result = {'texture': 'stone_axe.png', 'count': 1}
                found = True
            # Stone Axe Pattern 2 (Right-facing)
            elif (c[1] and c[2] and c[4] and c[5] and c[7] and
                c[1]['texture'] == 'stone.png' and c[2]['texture'] == 'stone.png' and c[5]['texture'] == 'stone.png' and
                c[4]['texture'] == 'stick.png' and c[7]['texture'] == 'stick.png'):
                crafting_result = {'texture': 'stone_axe.png', 'count': 1}
                found = True
        
        if not found:
            crafting_result = None
    # Stone Sword (2 Stone vertical + 1 Stick)
    elif stone_count == 2 and other_count == 1:
        c = crafting_grid
        # Check all 3 columns
        found = False
        for i in [0, 1, 2]:
            if (c[i] and c[i+3] and c[i+6] and
                c[i]['texture'] == 'stone.png' and c[i+3]['texture'] == 'stone.png' and
                c[i+6]['texture'] == 'stick.png'):
                crafting_result = {'texture': 'stone_sword.png', 'count': 1}
                found = True
                break
        if not found:
            crafting_result = None
    # Stone Shovel (1 Stone top + 2 Sticks)
    elif stone_count == 1 and other_count == 2:
        c = crafting_grid
        found = False
        for i in [0, 1, 2]:
            if (c[i] and c[i+3] and c[i+6] and
                c[i]['texture'] == 'stone.png' and c[i+3+0] and c[i+6+0] and # redundant but safe
                c[i+3]['texture'] == 'stick.png' and
                c[i+6]['texture'] == 'stick.png'):
                crafting_result = {'texture': 'stone_shovel.png', 'count': 1}
                found = True
                break
        if not found:
            crafting_result = None
    # --- IRON TOOLS (Iron Ingot + Sticks) ---
    # Iron Pickaxe (3 Iron top row + 2 Sticks center column)
    elif iron_ingot_count == 3 and other_count == 2:
        c = crafting_grid
        if (c[0] and c[1] and c[2] and c[4] and c[7] and
            c[0]['texture'] == 'iron_ingot.png' and c[1]['texture'] == 'iron_ingot.png' and c[2]['texture'] == 'iron_ingot.png' and
            c[4]['texture'] == 'stick.png' and c[7]['texture'] == 'stick.png'):
            crafting_result = {'texture': 'iron_pickaxe.png', 'count': 1}
        # Iron Axe Pattern 1 (Left-facing)
        elif (c[0] and c[1] and c[3] and c[4] and c[7] and
            c[0]['texture'] == 'iron_ingot.png' and c[1]['texture'] == 'iron_ingot.png' and c[3]['texture'] == 'iron_ingot.png' and
            c[4]['texture'] == 'stick.png' and c[7]['texture'] == 'stick.png'):
            crafting_result = {'texture': 'iron_axe.png', 'count': 1}
        # Iron Axe Pattern 2 (Right-facing)
        elif (c[1] and c[2] and c[4] and c[5] and c[7] and
            c[1]['texture'] == 'iron_ingot.png' and c[2]['texture'] == 'iron_ingot.png' and c[5]['texture'] == 'iron_ingot.png' and
            c[4]['texture'] == 'stick.png' and c[7]['texture'] == 'stick.png'):
            crafting_result = {'texture': 'iron_axe.png', 'count': 1}
        else:
            crafting_result = None
            
    # Iron Sword (2 Iron Ingots vertical + 1 Stick)
    elif iron_ingot_count == 2 and other_count == 1:
        c = crafting_grid
        found = False
        for i in [0, 1, 2]:
            if (c[i] and c[i+3] and c[i+6] and
                c[i]['texture'] == 'iron_ingot.png' and c[i+3]['texture'] == 'iron_ingot.png' and
                c[i+6]['texture'] == 'stick.png'):
                crafting_result = {'texture': 'iron_sword.png', 'count': 1}
                found = True
                break
        if not found:
            crafting_result = None
            
    # Iron Shovel (1 Iron top + 2 Sticks)
    elif iron_ingot_count == 1 and other_count == 2:
        c = crafting_grid
        found = False
        for i in [0, 1, 2]:
            if (c[i] and c[i+3] and c[i+6] and
                c[i]['texture'] == 'iron_ingot.png' and
                c[i+3]['texture'] == 'stick.png' and
                c[i+6]['texture'] == 'stick.png'):
                crafting_result = {'texture': 'iron_shovel.png', 'count': 1}
                found = True
                break
        if not found:
            crafting_result = None
    
    # --- IRON ARMOR (Iron Ingots only) ---
    # Iron Helmet (5 ingots: Top row + sides)
    elif iron_ingot_count == 5 and other_count == 0:
        c = crafting_grid
        if (c[0] and c[1] and c[2] and c[3] and c[5] and
            c[0]['texture'] == 'iron_ingot.png' and c[1]['texture'] == 'iron_ingot.png' and c[2]['texture'] == 'iron_ingot.png' and
            c[3]['texture'] == 'iron_ingot.png' and c[5]['texture'] == 'iron_ingot.png'):
            crafting_result = {'texture': 'iron_helmet.png', 'count': 1}
        # Iron Boots (4 ingots: Bottom sides)
        elif (c[3] and c[5] and c[6] and c[8] and
            c[3]['texture'] == 'iron_ingot.png' and c[5]['texture'] == 'iron_ingot.png' and
            c[6]['texture'] == 'iron_ingot.png' and c[8]['texture'] == 'iron_ingot.png'):
            crafting_result = {'texture': 'iron_boots.png', 'count': 1}
        else:
            crafting_result = None
    
    # Iron Leggings (7 ingots: all except middle and bottom-middle)
    elif iron_ingot_count == 7 and other_count == 0:
        c = crafting_grid
        if (c[0] and c[1] and c[2] and c[3] and c[5] and c[6] and c[8] and
            c[0]['texture'] == 'iron_ingot.png' and c[1]['texture'] == 'iron_ingot.png' and c[2]['texture'] == 'iron_ingot.png' and
            c[3]['texture'] == 'iron_ingot.png' and c[5]['texture'] == 'iron_ingot.png' and
            c[6]['texture'] == 'iron_ingot.png' and c[8]['texture'] == 'iron_ingot.png'):
            crafting_result = {'texture': 'iron_leggings.png', 'count': 1}
        else:
            crafting_result = None
            
    # Iron Chestplate (8 ingots: all except top-middle)
    elif iron_ingot_count == 8 and other_count == 0:
        c = crafting_grid
        if (c[0] and c[2] and c[3] and c[4] and c[5] and c[6] and c[7] and c[8] and
            c[0]['texture'] == 'iron_ingot.png' and c[2]['texture'] == 'iron_ingot.png' and 
            c[3]['texture'] == 'iron_ingot.png' and c[4]['texture'] == 'iron_ingot.png' and c[5]['texture'] == 'iron_ingot.png' and 
            c[6]['texture'] == 'iron_ingot.png' and c[7]['texture'] == 'iron_ingot.png' and c[8]['texture'] == 'iron_ingot.png'):
            crafting_result = {'texture': 'iron_chestplate.png', 'count': 1}
        else:
            crafting_result = None
    # --- DIAMOND TOOLS (Diamond + Sticks) ---
    # Diamond Pickaxe (3 Diamond top row + 2 Sticks center column)
    elif diamond_count == 3 and other_count == 2:
        c = crafting_grid
        if (c[0] and c[1] and c[2] and c[4] and c[7] and
            c[0]['texture'] == 'diamond.png' and c[1]['texture'] == 'diamond.png' and c[2]['texture'] == 'diamond.png' and
            c[4]['texture'] == 'stick.png' and c[7]['texture'] == 'stick.png'):
            crafting_result = {'texture': 'diamond_pickaxe.png', 'count': 1}
        # Diamond Axe Pattern 1 (Left-facing)
        elif (c[0] and c[1] and c[3] and c[4] and c[7] and
            c[0]['texture'] == 'diamond.png' and c[1]['texture'] == 'diamond.png' and c[3]['texture'] == 'diamond.png' and
            c[4]['texture'] == 'stick.png' and c[7]['texture'] == 'stick.png'):
            crafting_result = {'texture': 'diamond_axe.png', 'count': 1}
        # Diamond Axe Pattern 2 (Right-facing)
        elif (c[1] and c[2] and c[4] and c[5] and c[7] and
            c[1]['texture'] == 'diamond.png' and c[2]['texture'] == 'diamond.png' and c[5]['texture'] == 'diamond.png' and
            c[4]['texture'] == 'stick.png' and c[7]['texture'] == 'stick.png'):
            crafting_result = {'texture': 'diamond_axe.png', 'count': 1}
        else:
            crafting_result = None
            
    # Diamond Sword (2 Diamonds vertical + 1 Stick)
    elif diamond_count == 2 and other_count == 1:
        c = crafting_grid
        found = False
        for i in [0, 1, 2]:
            if (c[i] and c[i+3] and c[i+6] and
                c[i]['texture'] == 'diamond.png' and c[i+3]['texture'] == 'diamond.png' and
                c[i+6]['texture'] == 'stick.png'):
                crafting_result = {'texture': 'diamond_sword.png', 'count': 1}
                found = True
                break
        if not found:
            crafting_result = None
            
    # Diamond Shovel (1 Diamond top + 2 Sticks)
    elif diamond_count == 1 and other_count == 2:
        c = crafting_grid
        found = False
        for i in [0, 1, 2]:
            if (c[i] and c[i+3] and c[i+6] and
                c[i]['texture'] == 'diamond.png' and
                c[i+3]['texture'] == 'stick.png' and
                c[i+6]['texture'] == 'stick.png'):
                crafting_result = {'texture': 'diamond_shovel.png', 'count': 1}
                found = True
                break
        if not found:
            crafting_result = None
            
    # --- DIAMOND ARMOR (Diamonds only) ---
    # Diamond Helmet (5 diamonds: Top row + sides)
    elif diamond_count == 5 and other_count == 0:
        c = crafting_grid
        if (c[0] and c[1] and c[2] and c[3] and c[5] and
            c[0]['texture'] == 'diamond.png' and c[1]['texture'] == 'diamond.png' and c[2]['texture'] == 'diamond.png' and
            c[3]['texture'] == 'diamond.png' and c[5]['texture'] == 'diamond.png'):
            crafting_result = {'texture': 'diamond_helmet.png', 'count': 1}
        # Diamond Boots (4 diamonds: Bottom sides)
        elif (c[3] and c[5] and c[6] and c[8] and
            c[3]['texture'] == 'diamond.png' and c[5]['texture'] == 'diamond.png' and
            c[6]['texture'] == 'diamond.png' and c[8]['texture'] == 'diamond.png'):
            crafting_result = {'texture': 'diamond_boots.png', 'count': 1}
        else:
            crafting_result = None
    
    # Diamond Leggings (7 diamonds: all except middle and bottom-middle)
    elif diamond_count == 7 and other_count == 0:
        c = crafting_grid
        if (c[0] and c[1] and c[2] and c[3] and c[5] and c[6] and c[8] and
            c[0]['texture'] == 'diamond.png' and c[1]['texture'] == 'diamond.png' and c[2]['texture'] == 'diamond.png' and
            c[3]['texture'] == 'diamond.png' and c[5]['texture'] == 'diamond.png' and
            c[6]['texture'] == 'diamond.png' and c[8]['texture'] == 'diamond.png'):
            crafting_result = {'texture': 'diamond_leggings.png', 'count': 1}
        else:
            crafting_result = None
            
    # Diamond Chestplate (8 diamonds: all except top-middle)
    elif diamond_count == 8 and other_count == 0:
        c = crafting_grid
        if (c[0] and c[2] and c[3] and c[4] and c[5] and c[6] and c[7] and c[8] and
            c[0]['texture'] == 'diamond.png' and c[2]['texture'] == 'diamond.png' and 
            c[3]['texture'] == 'diamond.png' and c[4]['texture'] == 'diamond.png' and c[5]['texture'] == 'diamond.png' and 
            c[6]['texture'] == 'diamond.png' and c[7]['texture'] == 'diamond.png' and c[8]['texture'] == 'diamond.png'):
            crafting_result = {'texture': 'diamond_chestplate.png', 'count': 1}
        else:
            crafting_result = None
    else:
        crafting_result = None

# Performance & State variables
last_y = player.y
is_falling = False
fall_start_y = player.y
regen_timer = 0
update_timer = 0 # Timer to throttle heavy operations

# Performance Monitor
fps_text = Text(position=(0.75, 0.45), scale=1, origin=(0,0), color=color.black)
entity_count_text = Text(position=(0.75, 0.42), scale=1, origin=(0,0), color=color.black)

def spawn_wave(count):
    for i in range(count):
        # Spawn zombie at a distance (20-30 units away)
        angle = random.uniform(0, math.pi * 2)
        dist = random.uniform(20, 30)
        spawn_pos = player.position + Vec3(math.cos(angle) * dist, 0, math.sin(angle) * dist)
        # Ensure it's on ground level (y=1 based on Zombie class)
        spawn_pos.y = 1
        Zombie(position=spawn_pos)
    print(f"Wave {current_wave}: {count} Zombies appeared!")

def update():
    global health, last_y, is_falling, fall_start_y, regen_timer, selected_slot, update_timer, cursor_item, last_held_tex
    global is_breaking, breaking_timer, breaking_pos
    global current_wave, night_spawn_active
    
    # Day/Night Detection and Zombie Spawning
    if player.enabled:
        angle = sun.rotation_x % 360
        is_night = angle >= 180
        
        if is_night:
            if not night_spawn_active:
                # Transition to night: Start Wave 1
                night_spawn_active = True
                current_wave = 1
                spawn_wave(2)
            else:
                # Check if current wave is cleared to spawn next wave
                if 1 <= current_wave <= 2:
                    active_zombies = [e for e in scene.entities if isinstance(e, Zombie)]
                    if len(active_zombies) == 0:
                        if current_wave == 1:
                            current_wave = 2
                            spawn_wave(3)
                        elif current_wave == 2:
                            current_wave = 3
                            spawn_wave(5)
                elif current_wave == 3:
                    active_zombies = [e for e in scene.entities if isinstance(e, Zombie)]
                    if len(active_zombies) == 0:
                        current_wave = 4 # All waves done for this night
                        print("All night waves cleared!")
        else:
            # It's day
            if night_spawn_active:
                # Transition to day: Reset for next night
                night_spawn_active = False
                current_wave = 0
                # Optional: destroy remaining zombies during day (they should burn)
                for z in [e for e in scene.entities if isinstance(e, Zombie)]:
                    destroy(z)

    # Handle Block Breaking
    if is_breaking:
        # Check if we are still looking at the same block
        hit_info = raycast(camera.world_position, camera.forward, distance=5)
        current_pos = None
        if hit_info.hit:
            cp = hit_info.world_point - hit_info.normal * 0.5
            current_pos = (math.floor(cp[0]), math.floor(cp[1]), math.floor(cp[2]))
            
        if current_pos == breaking_pos:
            # Calculate breaking duration based on tool
            item = inventory[selected_slot]
            tex_name = world.voxels_get(breaking_pos)
            
            current_duration = 3.0 # Default Hand Speed for most blocks (dirt, grass, wood, planks)
            
            # 1. Block-Specific Overrides (Regardless of tool)
            if tex_name == 'leaves.png':
                current_duration = 0.5
            elif tex_name == 'glass.png':
                current_duration = 0.3
                
            # 2. Tool-Specific Overrides
            if item:
                t = item['texture']
                # Pickaxes for Stone, Iron, and Diamond
                if tex_name in ['stone.png', 'iron_ore.png', 'diamond_ore.png']:
                    if t == 'diamond_pickaxe.png':
                        if tex_name == 'stone.png': current_duration = 0.1
                        elif tex_name == 'iron_ore.png': current_duration = 0.7
                        elif tex_name == 'diamond_ore.png': current_duration = 0.5
                    elif t == 'iron_pickaxe.png':
                        current_duration = 0.5 if tex_name == 'stone.png' else 3.0
                    elif t == 'stone_pickaxe.png':
                        current_duration = 2.0 if tex_name == 'stone.png' else 5.0
                    elif t == 'wood_pickaxe.png':
                        current_duration = 5.0 if tex_name == 'stone.png' else 20.0
                    else:
                        current_duration = 20.0
                
                # Shovels for Soft Blocks
                elif tex_name in ['grass.png', 'dirt.png']:
                    if t == 'diamond_shovel.png':
                        current_duration = 0.1
                    elif t == 'iron_shovel.png':
                        current_duration = 0.3 # Fast!
                    elif t == 'stone_shovel.png':
                        current_duration = 0.75 # 4x faster than 3s
                    elif t == 'wood_shovel.png':
                        current_duration = 1.5 # 2x faster than 3s
                
                # Axes for Wood
                elif tex_name in ['wood.png', 'planks.png']:
                    if t == 'diamond_axe.png':
                        current_duration = 0.2
                    elif t == 'iron_axe.png':
                        current_duration = 0.5 # 6x faster than 3s
                    elif t == 'stone_axe.png':
                        current_duration = 0.75 # 4x faster than 3s
                    elif t == 'wood_axe.png':
                        current_duration = 1.5 # 2x faster than 3s
            else:
                # Common Hand Speed Defaults
                if tex_name in ['stone.png', 'iron_ore.png', 'diamond_ore.png']:
                    current_duration = 20.0
            
            breaking_timer += time.dt
            
            # Update crack visual stage (0-3)
            stage = int((breaking_timer / current_duration) * 4)
            stage = min(stage, 3)
            crack_overlay.texture_offset = crack_offsets[stage]
            
            # Continuous swinging while breaking
            if int(breaking_timer * 10) % 4 == 0:
                swing()

            # Break complete!
            if breaking_timer >= current_duration:
                is_breaking = False
                crack_overlay.disable()
                
                tex_name = world.voxels_get(breaking_pos)
                if tex_name:
                    # Harvest Requirement: Iron Ore needs Stone Pickaxe
                    can_harvest = True
                    if tex_name == 'iron_ore.png':
                        if not item or item['texture'] not in ['stone_pickaxe.png', 'iron_pickaxe.png', 'diamond_pickaxe.png']:
                            can_harvest = False
                    if tex_name == 'diamond_ore.png':
                        if not item or item['texture'] not in ['iron_pickaxe.png', 'diamond_pickaxe.png']:
                            can_harvest = False
                    
                    # Spawn Particles
                    for _ in range(12):
                        Particle(position=Vec3(breaking_pos) + Vec3(0,0.5,0), texture=tex_name)
                    
                    if can_harvest:
                        # Drop processed item if applicable
                        drop_tex = tex_name
                        if tex_name == 'iron_ore.png':
                            drop_tex = 'iron_ingot.png'
                        elif tex_name == 'diamond_ore.png':
                            drop_tex = 'diamond.png'
                            
                        # Stacking logic (Collect item)
                        stacked = False
                        max_s = get_max_stack(drop_tex)
                        for i in range(30):
                            if inventory[i] and inventory[i]['texture'] == drop_tex and inventory[i]['count'] < max_s:
                                inventory[i]['count'] += 1
                                stacked = True
                                break
                        if not stacked:
                            for i in range(30):
                                if inventory[i] == None:
                                    inventory[i] = {'texture': drop_tex, 'count': 1}
                                    stacked = True
                                    break
                        if stacked:
                            update_inventory_ui()
                    
                    # Only remove block if it can be harvested (for Iron Ore)
                    # For other blocks, they always break
                    if tex_name != 'iron_ore.png' or can_harvest:
                        world.remove_block(breaking_pos)
                breaking_timer = 0
        else:
            # Stopped looking at block, reset breaking
            is_breaking = False
            crack_overlay.disable()
            breaking_timer = 0

    # Update Held Item / Hand Visual only if changed
    item = inventory[selected_slot]
    current_tex = item['texture'] if item else 'hand.png'
    
    if current_tex != last_held_tex:
        last_held_tex = current_tex
        held_item.texture = current_tex
        
        if item:
            # Item vs Block scaling
            if item['texture'] in NON_BLOCKS:
                held_item.model = 'quad'
                held_item.scale = (0.4, 0.4, 1)
                held_item.rotation = (10, -20, 0)
                held_item.double_sided = True
            else:
                held_item.model = 'cube'
                held_item.scale = (0.2, 0.2, 0.2)
                held_item.rotation = (10, -20, 10)
                held_item.double_sided = False
        else:
            held_item.texture = 'hand.png'
            held_item.model = 'cube'
            held_item.scale = (0.2, 0.3, 0.1)
            held_item.rotation = (10, -20, 10)
            held_item.double_sided = False
    
    # Update Cursor Icon Position
    if cursor_item:
        cursor_icon.enabled = True
        cursor_icon.texture = cursor_item['texture']
        cursor_icon.position = (mouse.x, mouse.y)
    else:
        cursor_icon.enabled = False

    update_timer += time.dt
    
    # Update Performance Monitor
    if update_timer > 0.5:
        fps_text.text = f'FPS: {int(1/time.dt)}'
        entity_count_text.text = f'Ent: {len(scene.entities)}'
    
    # Day/Night Cycle (Throttle to run every few frames)
    if update_timer > 0.1:
        # Sun rotation
        sun.rotation_x += update_timer * 6 
        if sun.rotation_x > 360: sun.rotation_x = 0
        
        angle = sun.rotation_x % 360
        if angle < 180: # Day
            t = abs(angle-90)/90
            sky.color = color.rgb(
                lerp(color.cyan.r, color.black.r, t),
                lerp(color.cyan.g, color.black.g, t),
                lerp(color.cyan.b, color.black.b, t)
            )
        else: # Night
            sky.color = color.black

    # Selector logic (Throttle to run every 0.05s)
    if update_timer > 0.05:
        hit_info = raycast(camera.world_position, camera.forward, distance=5)
        if hit_info.hit:
            selector.enabled = True
            pos = hit_info.world_point - hit_info.normal * 0.5
            selector.position = (math.floor(pos[0]), math.floor(pos[1]), math.floor(pos[2]))
        else:
            selector.enabled = False
        
        # Reset timer after throttled operations
        if update_timer > 0.1: # Reset only after the longest throttle period has passed
            update_timer = 0

    for i in range(1, 6):
        if held_keys[str(i)]:
            selected_slot = i - 1
            update_inventory_ui()

    # Regeneration logic
    if health < 10:
        regen_timer += time.dt
        if regen_timer >= 5:
            health += 1
            regen_timer = 0
            update_health_ui()
    else:
        regen_timer = 0

    # Fall damage logic
    if not player.grounded:
        if not is_falling:
            is_falling = True
            fall_start_y = player.y
    else:
        if is_falling:
            is_falling = False
            fall_distance = fall_start_y - player.y
            if fall_distance > 3:
                damage = int(fall_distance - 3)
                take_damage(damage)
    
    # Respawn if fallen off world
    if player.y < -30:
        take_damage(health)

def update_health_ui():
    for i in range(len(hearts)):
        if i < health:
            hearts[i].enabled = True
        else:
            hearts[i].enabled = False
    update_armor_ui()

def update_armor_ui():
    pts = get_total_armor_points()
    for i in range(10):
        if i < math.ceil(pts / 2):
            armor_icons[i].enabled = True
        else:
            armor_icons[i].enabled = False

def get_total_armor_points():
    pts = 0
    for piece, item in equipped_armor.items():
        if item:
            pts += armor_values.get(item['texture'], 0)
    return pts

def take_damage(amount):
    global health
    pts = get_total_armor_points()
    reduction = pts * 0.04
    final_amount = amount * (1.0 - reduction)
    
    health -= final_amount
    update_health_ui()
    
    # Red flash effect for player
    camera.shake(duration=0.1, magnitude=0.1)
    
    if health <= 0:
        respawn()

def respawn():
    global health
    player.position = user_spawn_point
    health = 10
    update_health_ui()

# World System with Mesh Batching
# Chunk System
class Chunk(Entity):
    def __init__(self, position=(0,0,0), chunk_size=8):
        super().__init__(position=position)
        self.chunk_size = chunk_size
        self.voxels = {} # Local (x,y,z) -> texture
        self.batches = {} # texture -> Entity

    def build_mesh(self):
        # Clear existing batches
        for b in self.batches.values():
            destroy(b)
        self.batches = {}

        cx, cy, cz = self.position.x, self.position.y, self.position.z
        
        # Group voxels
        groups = {}
        for pos, tex in self.voxels.items():
            lx, ly, lz = pos
            # Global coordinates
            gx, gy, gz = int(cx + lx), int(cy + ly), int(cz + lz)
            
            neighbors = [
                (gx+1, gy, gz), (gx-1, gy, gz),
                (gx, gy+1, gz), (gx, gy-1, gz),
                (gx, gy, gz+1), (gx, gy, gz-1)
            ]
            
            is_visible = False
            for n in neighbors:
                if not world.voxels_get(n):
                    is_visible = True
                    break
            
            if is_visible:
                if tex not in groups: groups[tex] = []
                groups[tex].append(pos)

        # Create combined meshes
        for tex, positions in groups.items():
            temp_parent = Entity(enabled=False)
            for pos in positions:
                mdl = 'cube'
                if tex == 'crafting_table.png': mdl = 'crafting_table.obj'
                Entity(parent=temp_parent, model=mdl, position=pos, origin_y=-0.5)
            
            if temp_parent.children:
                self.batches[tex] = Entity(
                    parent=self,
                    model=temp_parent.combine(),
                    texture=tex,
                    collider='mesh'
                )
            destroy(temp_parent)

class World(Entity):
    def __init__(self):
        super().__init__()
        self.chunks = {} # (cx, cy, cz) -> Chunk
        self.chunk_size = 8

    def get_chunk_coord(self, pos):
        return (
            math.floor(pos[0] / self.chunk_size),
            math.floor(pos[1] / self.chunk_size),
            math.floor(pos[2] / self.chunk_size)
        )

    def get_local_coord(self, pos):
        return (
            int(pos[0] % self.chunk_size),
            int(pos[1] % self.chunk_size),
            int(pos[2] % self.chunk_size)
        )

    def add_block(self, pos, tex, sync=True):
        cx, cy, cz = self.get_chunk_coord(pos)
        lx, ly, lz = self.get_local_coord(pos)
        
        if (cx, cy, cz) not in self.chunks:
            self.chunks[(cx, cy, cz)] = Chunk(position=(cx*self.chunk_size, cy*self.chunk_size, cz*self.chunk_size), chunk_size=self.chunk_size)
        
        chunk = self.chunks[(cx, cy, cz)]
        chunk.voxels[(lx, ly, lz)] = tex
        
        if sync:
            self._sync_chunk_and_neighbors(pos)

    def remove_block(self, pos):
        cx, cy, cz = self.get_chunk_coord(pos)
        lx, ly, lz = self.get_local_coord(pos)
        
        if (cx, cy, cz) in self.chunks:
            chunk = self.chunks[(cx, cy, cz)]
            if (lx, ly, lz) in chunk.voxels:
                del chunk.voxels[(lx, ly, lz)]
                self._sync_chunk_and_neighbors(pos)

    def _sync_chunk_and_neighbors(self, pos):
        cx, cy, cz = self.get_chunk_coord(pos)
        lx, ly, lz = self.get_local_coord(pos)
        
        # Re-mesh the current chunk
        if (cx, cy, cz) in self.chunks:
            self.chunks[(cx, cy, cz)].build_mesh()
        
        # Re-mesh neighbor chunks if block is on the boundary
        neighbors = [
            (lx == 0, (cx-1, cy, cz)),
            (lx == self.chunk_size-1, (cx+1, cy, cz)),
            (ly == 0, (cx, cy-1, cz)),
            (ly == self.chunk_size-1, (cx, cy+1, cz)),
            (lz == 0, (cx, cy, cz-1)),
            (lz == self.chunk_size-1, (cx, cy, cz+1))
        ]
        
        for is_boundary, n_coord in neighbors:
            if is_boundary and n_coord in self.chunks:
                self.chunks[n_coord].build_mesh()

    def voxels_get(self, pos):
        # Helper to check if a block exists globally
        cx, cy, cz = self.get_chunk_coord(pos)
        lx, ly, lz = self.get_local_coord(pos)
        if (cx, cy, cz) in self.chunks:
            return self.chunks[(cx, cy, cz)].voxels.get((lx, ly, lz))
        return None

world = World()

def toggle_pause():
    global game_state
    if game_state == 'PLAYING':
        game_state = 'PAUSED'
        pause_menu.enabled = True
        mouse.locked = False
        player.enabled = False
    elif game_state == 'PAUSED':
        game_state = 'PLAYING'
        pause_menu.enabled = False
        mouse.locked = True
        player.enabled = True

def save_world(name):
    world_data = {
        'player_pos': (player.x, player.y, player.z),
        'inventory': inventory,
        'voxels': []
    }
    # Collect all voxels from all chunks
    for chunk_coord, chunk in world.chunks.items():
        for local_pos, tex in chunk.voxels.items():
            # Convert to global coord
            global_pos = (
                chunk_coord[0] * 8 + local_pos[0],
                chunk_coord[1] * 8 + local_pos[1],
                chunk_coord[2] * 8 + local_pos[2]
            )
            world_data['voxels'].append({'pos': global_pos, 'tex': tex})
            
    if not os.path.exists('worlds'):
        os.makedirs('worlds')
        
    with open(f'worlds/{name}.json', 'w') as f:
        json.dump(world_data, f)
    print(f"World {name} saved with {len(world_data['voxels'])} voxels!")

def load_world(name):
    global inventory, current_world_name, health
    path = f'worlds/{name}.json'
    if not os.path.exists(path):
        print(f"World {name} not found!")
        return False
        
    with open(path, 'r') as f:
        data = json.load(f)
        
    # Clear current world
    for chunk in list(world.chunks.values()):
        destroy(chunk)
    world.chunks = {}
    
    # Restore Data
    p_pos = data.get('player_pos', (30, 6, 30)) # Center of 60x60
    player.position = Vec3(p_pos[0], p_pos[1], p_pos[2])
    inventory = data.get('inventory', [{'texture': 'grass.png', 'count': 64}] + [None] * 29)
    # Ensure all slots are present
    if len(inventory) < 30:
        inventory += [None] * (30 - len(inventory))
    
    # Reset hearts
    health = 10 
    
    # Recreate Voxels
    v_list = data.get('voxels', [])
    for v in v_list:
        world.add_block(tuple(v['pos']), v['tex'], sync=False)
        
    current_world_name = name
    world_name_text.text = f"World: {name}"
    world_name_text.enabled = True
    update_inventory_ui()
    
    # Non-blocking mesh build
    print(f"World {name} loaded. Building meshes for {len(world.chunks)} chunks...")
    loading_text.enabled = True
    
    chunks_to_build = list(world.chunks.values())
    
    def build_chunk_step(index):
        if index >= len(chunks_to_build):
            loading_text.enabled = False
            print(f"Finished loading world {name}")
            return
        
        # Build 10 chunks per frame to keep it responsive but fast
        for i in range(index, min(index + 10, len(chunks_to_build))):
            chunks_to_build[i].build_mesh()
        
        invoke(build_chunk_step, index + 10, delay=0.01)

    build_chunk_step(0)
    return True

def start_new_game():
    loading_text.enabled = True
    invoke(start_new_game_impl, delay=0.1)

def start_new_game_impl():
    global game_state, current_world_name, inventory
    # Find next available name World_N
    if not os.path.exists('worlds'):
        os.makedirs('worlds')
    
    existing = os.listdir('worlds')
    i = 1
    while f"World_{i}.json" in existing:
        i += 1
    new_name = f"World_{i}"
    
    # Reset / Clear world
    for chunk in list(world.chunks.values()):
        destroy(chunk)
    world.chunks = {}
    
    # Reset inventory for new game
    inventory = [{'texture': 'grass.png', 'count': 64}] + [None] * 29
    player.position = Vec3(20, 6, 20)
    
    generate_base_world()
    
    game_state = 'PLAYING'
    menu_parent.enabled = False
    player.enabled = True
    mouse.locked = True
    current_world_name = new_name
    world_name_text.text = f"World: {new_name}"
    world_name_text.enabled = True
    update_inventory_ui()
    loading_text.enabled = False

def load_game(name):
    loading_text.enabled = True
    invoke(load_game_impl, name, delay=0.1)

def load_game_impl(name):
    global game_state
    if load_world(name):
        game_state = 'PLAYING'
        menu_parent.enabled = False
        player.enabled = True
        mouse.locked = True
    loading_text.enabled = False

def save_and_quit():
    save_world(current_world_name)
    # Return to menu
    global game_state
    game_state = 'MENU'
    pause_menu.enabled = False
    menu_parent.enabled = True
    world_name_text.enabled = False
    player.enabled = False
    mouse.locked = False
    refresh_menu_worlds()

def upgrade_current_world():
    loading_text.enabled = True
    invoke(upgrade_current_world_impl, delay=0.1)

def upgrade_current_world_impl():
    save_world(current_world_name) # Save current first
    if upgrade_world_file(current_world_name):
        load_world(current_world_name) # Reload with new area
        print(f"World {current_world_name} updated and expanded!")
    loading_text.enabled = False

def upgrade_world_file(name):
    path = f'worlds/{name}.json'
    if not os.path.exists(path):
        return False
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    voxels = data.get('voxels', [])
    pos_set = set(tuple(v['pos']) for v in voxels)
    
    # 0. Cave Definition
    cave_centers = []
    for _ in range(40):
        cx, cy, cz = random.randint(0, 59), random.randint(-15, 2), random.randint(0, 59)
        cr = random.uniform(2, 5)
        # Bounding box for cave
        cave_centers.append({
            'c': (cx, cy, cz), 'r': cr, 'r_sq': cr**2,
            'bbox': (cx-cr, cx+cr, cy-cr, cy+cr, cz-cr, cz+cr)
        })

    def is_in_cave(x, y, z):
        for cave in cave_centers:
            bb = cave['bbox']
            if x >= bb[0] and x <= bb[1] and y >= bb[2] and y <= bb[3] and z >= bb[4] and z <= bb[5]:
                cx, cy, cz = cave['c']
                if (x-cx)**2 + (y-cy)**2 + (z-cz)**2 < cave['r_sq']:
                    return True
        return False

    added_count = 0
    # 1. Expand (60x60)
    for z in range(60):
        for x in range(60):
            # Surface
            if (x, 0, z) not in pos_set:
                if not is_in_cave(x, 0, z):
                    voxels.append({'pos': [x, 0, z], 'tex': 'grass.png'})
                    added_count += 1
                elif random.random() < 0.05:
                    voxels.append({'pos': [x, 0, z], 'tex': 'iron_ore.png'})
                    added_count += 1
            
            # Subsurface
            for y in range(-1, -17, -1):
                if (x, y, z) not in pos_set:
                    in_cave = is_in_cave(x, y, z)
                    if not in_cave:
                        if y >= -2: tex = 'dirt.png'
                        else:
                            tex = 'stone.png'
                            r = random.random()
                            if r < 0.02: tex = 'diamond_ore.png'
                            elif r < 0.07: tex = 'iron_ore.png'
                        voxels.append({'pos': [x, y, z], 'tex': tex})
                        added_count += 1
                    else:
                        # Cave ores
                        r = random.random()
                        if y <= -3:
                            if r < 0.01: 
                                voxels.append({'pos': [x, y, z], 'tex': 'diamond_ore.png'})
                                added_count += 1
                            elif r < 0.04:
                                voxels.append({'pos': [x, y, z], 'tex': 'iron_ore.png'})
                                added_count += 1
                        elif r < 0.02:
                            voxels.append({'pos': [x, y, z], 'tex': 'iron_ore.png'})
                            added_count += 1
    
    # 2. Add trees for expansion
    tree_spots = [(5, 5), (15, 15), (10, 15), (25, 10), (30, 30), (35, 5), (5, 35), (20, 25),
                  (45, 45), (50, 10), (10, 50), (40, 20), (55, 55), (20, 45)]
    for tx, tz in tree_spots:
        # Just check the base wood block to see if tree exists
        if (tx, 1, tz) not in pos_set:
            # Trunk
            for ty in range(1, 5):
                voxels.append({'pos': [tx, ty, tz], 'tex': 'wood.png'})
                added_count += 1
            # Leaves
            for dx in range(-1, 2):
                for dy in range(4, 6):
                    for dz in range(-1, 2):
                        if (dx, dy, dz) != (0, dy, 0):
                            lx, ly, lz = tx + dx, dy, tz + dz
                            voxels.append({'pos': [lx, ly, lz], 'tex': 'leaves.png'})
                            added_count += 1

    # 3. Upgrade stones to diamonds (Random chance for any stone)
    upgraded_count = 0
    for v in voxels:
        if v['tex'] == 'stone.png' and -17 <= v['pos'][1] <= -3:
            if random.random() < 0.01: # Reduced to 1% since we have more area
                v['tex'] = 'diamond_ore.png'
                upgraded_count += 1
                
    data['voxels'] = voxels
    with open(path, 'w') as f:
        json.dump(data, f)
    
    print(f"Upgraded {name}: Added {added_count} blocks and {upgraded_count} diamonds!")
    return True

def generate_base_world():
    # 0. Cave Definition
    cave_centers = []
    for _ in range(40): # More caves for better connectivity
        cx, cy, cz = random.randint(0, 59), random.randint(-15, 2), random.randint(0, 59)
        cr = random.uniform(2, 5)
        cave_centers.append({
            'c': (cx, cy, cz), 'r_sq': cr**2,
            'bbox': (cx-cr, cx+cr, cy-cr, cy+cr, cz-cr, cz+cr)
        })

    def is_in_cave(x, y, z):
        for cave in cave_centers:
            bb = cave['bbox']
            if x >= bb[0] and x <= bb[1] and y >= bb[2] and y <= bb[3] and z >= bb[4] and z <= bb[5]:
                cx, cy, cz = cave['c']
                if (x-cx)**2 + (y-cy)**2 + (z-cz)**2 < cave['r_sq']:
                    return True
        return False

    # Create ground
    for i in range(60):
        for j in range(60):
            # Surface
            # Punch holes in surface for cave entrances
            if not is_in_cave(j, 0, i):
                world.add_block((j, 0, i), 'grass.png', sync=False)
            elif is_in_cave(j, 0, i) and random.random() < 0.05:
                # Occasional floating ore in entrance
                world.add_block((j, 0, i), 'iron_ore.png', sync=False)
            
            # Dirt
            for y in [-1, -2]:
                in_cave = is_in_cave(j, y, i)
                if not in_cave:
                    world.add_block((j, y, i), 'dirt.png', sync=False)
                elif in_cave and random.random() < 0.02:
                     # Rare cave ore in dirt layer
                     world.add_block((j, y, i), 'iron_ore.png', sync=False)
            
            # Stone
            for y in range(-3, -17, -1):
                in_cave = is_in_cave(j, y, i)
                if not in_cave:
                    tex = 'stone.png'
                    r = random.random()
                    if r < 0.02: # 2% chance of diamond ore
                        tex = 'diamond_ore.png'
                    elif r < 0.07: # 5% chance of iron ore
                        tex = 'iron_ore.png'
                    world.add_block((j, y, i), tex, sync=False)
                elif in_cave:
                    # Sparse ores "floating" or on cave walls
                    r = random.random()
                    if r < 0.01: # 1% diamond inside cave
                        world.add_block((j, y, i), 'diamond_ore.png', sync=False)
                    elif r < 0.04: # 3% iron inside cave
                        world.add_block((j, y, i), 'iron_ore.png', sync=False)

    def create_tree(x, z):
        for y in range(1, 5):
            world.add_block((x, y, z), 'wood.png', sync=False)
        for x_off in range(-1, 2):
            for y_off in range(4, 6):
                for z_off in range(-1, 2):
                    if (x + x_off, y_off, z + z_off) != (x, y_off, z):
                        world.add_block((x + x_off, y_off, z + z_off), 'leaves.png', sync=False)

    # Distributed trees for 60x60 area
    tree_spots = [(5, 5), (15, 15), (10, 15), (25, 10), (30, 30), (35, 5), (5, 35), (20, 25),
                  (45, 45), (50, 10), (10, 50), (40, 20), (55, 55), (20, 45)]
    for tx, tz in tree_spots:
        create_tree(tx, tz)

    # Build all chunks after generation
    for chunk in world.chunks.values():
        chunk.build_mesh()

# --- UI SYSTEMS ---

# Main Menu UI
menu_parent = Entity(parent=camera.ui)
title = Text(text="BeboCraft", parent=menu_parent, scale=5, position=(0, 0.4), origin=(0, 0))
new_btn = Button(text="New World", parent=menu_parent, scale=(0.3, 0.1), position=(0, 0.2), on_click=start_new_game)

loading_text = Text(text="Loading...", parent=camera.ui, scale=3, position=(0, 0), origin=(0, 0), enabled=False, color=color.azure)

world_list_parent = Entity(parent=menu_parent, position=(0, -0.1))
world_buttons = []

def refresh_menu_worlds():
    for b in world_buttons:
        destroy(b)
    world_buttons.clear()
    
    if not os.path.exists('worlds'):
        return
        
    world_files = [f for f in os.listdir('worlds') if f.endswith('.json')]
    for i, f in enumerate(world_files):
        name = f.replace('.json', '')
        btn = Button(
            text=name, 
            parent=world_list_parent, 
            scale=(0.3, 0.08), 
            position=(0, -i * 0.1), 
            on_click=Func(load_game, name)
        )
        world_buttons.append(btn)

refresh_menu_worlds()

# Pause Menu UI
pause_menu = Entity(parent=camera.ui, enabled=False)
pause_bg = Entity(parent=pause_menu, model='quad', scale=(2, 2), color=color.black66)
resume_btn = Button(text="Resume", parent=pause_menu, scale=(0.3, 0.1), position=(0, 0.2), on_click=toggle_pause)
upgrade_btn = Button(text="Update World (Expand & Gems)", parent=pause_menu, scale=(0.4, 0.1), position=(0, 0.05), on_click=upgrade_current_world)
save_quit_btn = Button(text="Save & Quit", parent=pause_menu, scale=(0.3, 0.1), position=(0, -0.1), on_click=save_and_quit)

# Update UI and Run
update_inventory_ui()

def on_application_quit():
    if game_state != 'MENU':
        save_world(current_world_name)

app.run()
