# ECHOFRONTIER - Sci-Fantasy Action RPG

A complete, playable action RPG built in Python with Pygame, featuring procedural dungeons, Echo Fragment progression system, multiple biomes, bosses, and deep build customization.

![Game Characters](provided by user)

## Features

### Core Gameplay
- **Fast-paced Action Combat** - Hack-and-slash with dodge mechanics
- **Echo Fragment System** - Classless progression with mix-and-match abilities
- **Procedural Dungeons** - Unique layouts every run
- **Multiple Biomes** - Void Ruins, Floating Forests, Reality Tears
- **Boss Encounters** - Multi-phase bosses with unique mechanics
- **Loot & Gear** - Weapons, armor, and accessories with random affixes
- **Persistent Progression** - Account-level Echo Rank system
- **Hub Town** - Safe zone with NPCs, vendors, and Echo Forge

### Game Systems
1. **Combat** - Real-time action with attack, dodge, and abilities
2. **Echo Fragments** - Core (class), Active (abilities), Passive (stats)
3. **Enemies** - 6+ unique enemy types with special behaviors
4. **Bosses** - 3 unique bosses with phase transitions
5. **Procedural Generation** - Room-based dungeons with corridors
6. **Loot** - 5 rarity tiers (Common to Legendary) with affixes
7. **Progression** - Level up, gain stats, unlock new fragments
8. **Hub NPCs** - Lorekeeper, Vendor, Forge Master, Quest Giver

## Installation

### Requirements
- Python 3.8+
- Pygame 2.5.0+

### Setup

1. **Install Python** (if not already installed)
   - Download from [python.org](https://www.python.org/downloads/)
   - Make sure to check "Add Python to PATH" during installation

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

   Or manually:
   ```bash
   pip install pygame
   ```

3. **Run the Game**
   ```bash
   cd game
   python main.py
   ```

## Controls

### Movement
- **W/A/S/D** or **Arrow Keys** - Move character
- **Mouse** - Aim direction

### Combat
- **Left Click** - Basic attack
- **Space** - Dodge/Roll (with invulnerability frames)
- **Q** - Ability 1
- **E** - Ability 2
- **R** - Ability 3
- **F** - Ability 4 / Interact with NPCs

### Interface
- **I** - Open/Close Inventory
- **ESC** - Pause Menu
- **Enter** - Enter dungeon (at gate in hub)

## Gameplay Guide

### Starting Out

1. **Hub Town** - You begin in Echo Sanctuary
   - Talk to NPCs with **F** key when nearby
   - Visit the **Fragment Merchant** to see available items
   - Approach the **Dungeon Gate** and press **Enter** to start a run

2. **Dungeon Runs**
   - Clear rooms of enemies
   - Collect loot (glowing items)
   - Defeat the boss to complete the floor
   - Death drops your Core Fragment (Legacy system)

3. **Progression**
   - Gain XP by defeating enemies and clearing rooms
   - Level up to increase stats
   - Unlock new Echo Fragments
   - Increase Echo Rank for account-wide progression

### Echo Fragment System

**Core Fragments** (Choose 1)
- Shadowblade Core - Swift melee specialist
- Solar Mystic Core - Healing and energy
- Chrono Warrior Core - Time manipulation

**Active Abilities** (Equip up to 4)
- Phantom Step - Teleport forward
- Void Surge - AoE explosion
- Solar Lance - Piercing beam
- Radiant Heal - Self-heal
- Time Slow - Slow enemies in area
- Temporal Echo - Create clone

**Passive Fragments** (Equip up to 5)
- Lifesteal Shard - Heal on hit
- Void Armor - Defense boost
- Solar Blessing - Health regen
- Swift Steps - Movement speed
- Critical Mind - Crit chance/damage
- Power Surge - Attack power

### Enemy Types

1. **Lantern Crawler** (Void) - Disorienting pulses
2. **Echo Leech** (Void) - Drains ability cooldowns
3. **Phase Blade** (Void) - Teleports to player
4. **Thornstalker** (Forest) - Burrows and ambushes
5. **Time Shard** (Crystal) - Creates slow fields
6. **Basic Enemy** - Standard melee

### Bosses

1. **The Broken Aegis** (Void Ruins)
   - Gravity Slam attacks
   - Pulls player in
   - Increases speed in later phases

2. **Lyra's Eclipse** (Floating Forests)
   - Spawns healing Solar Blooms
   - Destroy blooms to prevent healing
   - More aggressive as health drops

3. **Chronomancer's Core** (Reality Tears)
   - Rewinds time to restore health
   - Save high damage for after rewind
   - May spawn temporal clones

### Biomes

1. **Corrupted Void Ruins**
   - Purple/dark aesthetic
   - Void-type enemies
   - Boss: The Broken Aegis

2. **Lush Floating Forests** (Unlock at Echo Rank 3)
   - Green/natural aesthetic
   - Forest creatures
   - Boss: Lyra's Eclipse

3. **Crystallized Reality Tears** (Unlock at Echo Rank 5)
   - Blue/crystalline aesthetic
   - Time-based enemies
   - Boss: Chronomancer's Core

### Loot System

**Rarity Tiers**
- Common (Gray) - Basic stats
- Uncommon (Green) - 1 affix
- Rare (Blue) - 2 affixes
- Epic (Purple) - 3 affixes
- Legendary (Gold) - 4 affixes + unique effects

**Item Types**
- Weapons - Increase damage
- Armor (Head/Chest/Legs/Boots) - Defense
- Accessories (Rings/Amulets) - Mixed bonuses

**Affixes Examples**
- +Damage
- +% Damage
- +Attack Speed
- +Max Health
- +Critical Chance
- +Movement Speed
- +Cooldown Reduction

## Tips & Strategies

1. **Learn Enemy Patterns** - Each enemy has tells before attacking
2. **Use Dodge Wisely** - I-frames during roll, but has cooldown
3. **Build Synergies** - Combine fragments that work together
4. **Clear Rooms Fully** - More XP and loot
5. **Upgrade at Hub** - Visit Forge Master to upgrade fragments
6. **Experiment with Builds** - Different fragments = different playstyles
7. **Boss Phases** - Bosses change behavior at 75%, 50%, 25% health
8. **Collect Loot** - Walk over glowing items to collect

## Save System

- Progress automatically saves when returning to hub
- Account progression (Echo Rank, unlocks) persists
- Save file location: `save/progress.json`

## Troubleshooting

**Game won't start**
- Make sure Pygame is installed: `pip install pygame`
- Check Python version: `python --version` (needs 3.8+)

**Performance issues**
- Close other applications
- Reduce number of enemies in dungeons (edit dungeon.py)

**Display issues**
- Game runs at 1280x720 resolution
- Windowed mode only (can be changed in main.py)

## Development

Built with:
- Python 3.x
- Pygame 2.5.0
- Pure Python (no external assets initially)

All systems implemented:
- ✅ Player controller with combat
- ✅ Enemy AI and behaviors
- ✅ Boss encounters with phases
- ✅ Procedural dungeon generation
- ✅ Echo Fragment system
- ✅ Loot and gear
- ✅ Progression and leveling
- ✅ Hub town with NPCs
- ✅ Particle effects
- ✅ UI and HUD
- ✅ Camera system
- ✅ Save/load system

## Credits

**ECHOFRONTIER** - Developed as a complete Python game prototype

Game Design Document based on extensive RPG systems design including:
- Character concepts and lore
- Echo Fragment progression
- Biome and enemy design
- Boss mechanics
- Hub systems

## License

This is a prototype/demo game. Feel free to modify and extend!

---

## Quick Start Summary

```bash
# Install
pip install pygame

# Run
cd game
python main.py

# Play
- Move with WASD
- Attack with Left Click
- Dodge with Space
- Use abilities with Q/E/R/F
- Press Enter at gate to start dungeon
- Press I for inventory
- Have fun!
```

Enjoy exploring the Orivian ruins and building your perfect Echo-Seeker!
