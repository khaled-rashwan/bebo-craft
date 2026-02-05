<<<<<<< HEAD
# bebo-craft
# ⛏️ BeboCraft - A High-Performance Python Voxel Engine  BeboCraft is a feature-rich, high-performance voxel game built with Python and the **Ursina Engine**. It features a modern chunk-based rendering system, procedural world generation, and advanced gameplay mechanics inspired by classic sandbox games.
=======
# ⛏️ BeboCraft - A High-Performance Python Voxel Engine

BeboCraft is a feature-rich, high-performance voxel game built with Python and the **Ursina Engine**. It features a modern chunk-based rendering system, procedural world generation, and advanced gameplay mechanics inspired by classic sandbox games.

## 🚀 Key Features

### 🌍 Advanced World Generation
*   **Massive Discovery**: Procedural generation of a 60x60 playable area with seamless chunk transitions.
*   **Procedural Caves**: Dynamic cave systems carved out of deep stone layers, perfect for specialized mining operations.
*   **Deep Stratigraphy**: Multi-layered world structure including Grass, Dirt, Stone, Iron Ore, and Diamond Ore.
*   **Smart Expansion**: An intelligent "World Upgrade" system that expands existing saved worlds while preserving user-built structures.

### ⚡ Technical Excellence
*   **Face Culling Engine**: A global neighbor-checking mesh builder that hides internal voxel faces, drastically reducing polygon counts and ensuring high FPS even on modest hardware.
*   **Batch Rendering**: Chunk-based mesh batching with asynchronous building to keep the UI responsive during world loading.
*   **Dynamic Lighting**: Real-time day/night cycle with smooth sky transitions.

### 🛠️ Gameplay Mechanics
*   **Inventory & Crafting**: Comprehensive item system with 30-slot inventory, hotbar selection, and a functional crafting table.
*   **Tool Progression**: Tiered equipment (Wood, Stone, Iron, Diamond) with unique durability and harvest requirements.
*   **Armor System**: Equipable armor (Helmets, Chestplates, Leggings, Boots) that provide visible UI feedback and actual damage reduction.
*   **Mob AI System**: Dynamic Zombie spawns with AI pathfinding, attack logic, and a player health/regeneration system.

## 📥 Getting Started

### Prerequisites
*   Python 3.10+
*   `ursina` library

## 📁 Project Structure
*   `main.py`: The primary entry point for the game.
*   `textures/`: All block and UI textures.
*   `models/`: 3D models and compressed assets.
*   `scripts/`: Utility and generation tools for developers.
*   `worlds/`: Saved game data (local only).

### Installation
1. Clone the repository: `git clone <repo-url>`
2. Install dependencies: `pip install ursina`
3. Launch the game: `python main.py`

---
*Built with passion for the voxel community.*
>>>>>>> e4c643d (Initial commit: 60x60 world expansion, procedural caves, and performance optimization engine)
