"""
Shop and Vendor System - Buy/sell items, upgrade fragments
"""

import pygame
from items import LootGenerator, Weapon, Armor, Accessory
from echo_system import EchoLibrary

class ShopItem:
    """Item for sale in shop"""

    def __init__(self, item, price):
        self.item = item
        self.price = price

class Shop:
    """Base shop class"""

    def __init__(self, shop_type="General"):
        self.shop_type = shop_type
        self.inventory = []
        self.refresh_shop()

    def refresh_shop(self):
        """Generate new shop inventory"""
        self.inventory.clear()

        loot_gen = LootGenerator()

        if self.shop_type == "Weapon":
            # Weapon shop
            for i in range(6):
                weapon = loot_gen.generate_weapon(level=2 + i, biome="Void")
                price = self.calculate_price(weapon)
                self.inventory.append(ShopItem(weapon, price))

        elif self.shop_type == "Armor":
            # Armor shop
            slots = ["head", "chest", "legs", "boots"]
            for slot in slots:
                armor = loot_gen.generate_armor(level=3, slot=slot)
                price = self.calculate_price(armor)
                self.inventory.append(ShopItem(armor, price))

        elif self.shop_type == "Fragment":
            # Echo Fragment shop
            library = EchoLibrary()

            # Sell some fragments
            fragment_names = [
                "Void Surge", "Solar Lance", "Radiant Heal",
                "Lifesteal Shard", "Void Armor", "Swift Steps"
            ]

            for name in fragment_names:
                fragment = library.get_fragment(name)
                if fragment:
                    price = 150 + (50 * fragment.level)
                    self.inventory.append(ShopItem(fragment, price))

        elif self.shop_type == "Potion":
            # Potion shop
            potions = [
                ("Health Potion", 50, "potion_health"),
                ("Mana Potion", 40, "potion_mana"),
                ("Speed Potion", 60, "potion_speed"),
                ("Strength Potion", 70, "potion_strength")
            ]

            for potion_name, price, potion_type in potions:
                # Create simple potion object
                potion = type('Potion', (), {
                    'name': potion_name,
                    'item_type': potion_type,
                    'get_rarity_color': lambda: (100, 200, 255)
                })()

                self.inventory.append(ShopItem(potion, price))

    def calculate_price(self, item):
        """Calculate item price based on rarity and level"""
        base_prices = {
            "Common": 25,
            "Uncommon": 75,
            "Rare": 200,
            "Epic": 500,
            "Legendary": 1500
        }

        base = base_prices.get(item.rarity, 50)

        # Add level multiplier
        level_mult = getattr(item, 'level', 1)

        return int(base * level_mult)

    def buy_item(self, index, player):
        """Player buys item"""
        if index < 0 or index >= len(self.inventory):
            return False, "Invalid item"

        shop_item = self.inventory[index]

        if player.gold < shop_item.price:
            return False, "Not enough gold!"

        # Purchase
        player.gold -= shop_item.price

        print(f"Purchased {shop_item.item.name} for {shop_item.price} gold")

        # TODO: Add item to player inventory
        # For now, just confirm purchase

        # Remove from shop (limited stock)
        self.inventory.pop(index)

        return True, f"Bought {shop_item.item.name}!"

class ShopUI:
    """UI for shop interaction"""

    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.active_shop = None
        self.is_open = False
        self.selected_index = 0
        self.scroll_offset = 0

        # Fonts
        self.font_small = pygame.font.Font(None, 18)
        self.font_medium = pygame.font.Font(None, 24)
        self.font_large = pygame.font.Font(None, 36)

        # Colors
        self.color_bg = (30, 25, 40)
        self.color_panel = (50, 45, 60)
        self.color_highlight = (100, 150, 200)
        self.color_text = (220, 220, 220)

    def open_shop(self, shop):
        """Open shop UI"""
        self.active_shop = shop
        self.is_open = True
        self.selected_index = 0
        self.scroll_offset = 0

    def close_shop(self):
        """Close shop UI"""
        self.is_open = False
        self.active_shop = None

    def handle_event(self, event, player):
        """Handle shop input"""
        if not self.is_open:
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.close_shop()

            elif event.key == pygame.K_UP:
                self.selected_index = max(0, self.selected_index - 1)

            elif event.key == pygame.K_DOWN:
                if self.active_shop:
                    self.selected_index = min(len(self.active_shop.inventory) - 1, self.selected_index + 1)

            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                # Buy selected item
                if self.active_shop:
                    success, message = self.active_shop.buy_item(self.selected_index, player)
                    print(message)

                    if not success and self.selected_index >= len(self.active_shop.inventory):
                        self.selected_index = max(0, len(self.active_shop.inventory) - 1)

    def render(self, screen, player):
        """Render shop UI"""
        if not self.is_open or not self.active_shop:
            return

        # Background overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        # Shop panel
        panel_width = 700
        panel_height = 550
        panel_x = (self.screen_width - panel_width) // 2
        panel_y = (self.screen_height - panel_height) // 2

        pygame.draw.rect(screen, self.color_panel, (panel_x, panel_y, panel_width, panel_height))
        pygame.draw.rect(screen, self.color_highlight, (panel_x, panel_y, panel_width, panel_height), 3)

        # Title
        title = self.font_large.render(f"{self.active_shop.shop_type} Shop", True, self.color_text)
        screen.blit(title, (panel_x + 20, panel_y + 20))

        # Player gold
        gold_text = self.font_medium.render(f"Gold: {player.gold}", True, (255, 215, 0))
        screen.blit(gold_text, (panel_x + panel_width - 150, panel_y + 25))

        # Items
        item_y = panel_y + 80
        item_height = 60

        for i, shop_item in enumerate(self.active_shop.inventory):
            if i < self.scroll_offset:
                continue
            if item_y > panel_y + panel_height - 100:
                break

            # Item background
            if i == self.selected_index:
                bg_color = (80, 100, 140)
            else:
                bg_color = (60, 55, 70)

            pygame.draw.rect(screen, bg_color, (panel_x + 20, item_y, panel_width - 40, item_height - 5))

            # Item name
            name_color = shop_item.item.get_rarity_color() if hasattr(shop_item.item, 'get_rarity_color') else (220, 220, 220)
            name_text = self.font_medium.render(shop_item.item.name, True, name_color)
            screen.blit(name_text, (panel_x + 40, item_y + 10))

            # Item type/rarity
            if hasattr(shop_item.item, 'rarity'):
                info_text = self.font_small.render(f"{shop_item.item.rarity} {shop_item.item.item_type}", True, (180, 180, 180))
                screen.blit(info_text, (panel_x + 40, item_y + 35))

            # Price
            can_afford = player.gold >= shop_item.price
            price_color = (100, 255, 100) if can_afford else (255, 100, 100)
            price_text = self.font_medium.render(f"{shop_item.price}g", True, price_color)
            screen.blit(price_text, (panel_x + panel_width - 150, item_y + 18))

            item_y += item_height

        # Instructions
        instructions = [
            "↑↓ - Select",
            "ENTER - Buy",
            "ESC - Close"
        ]

        inst_y = panel_y + panel_height - 70
        for instruction in instructions:
            inst_text = self.font_small.render(instruction, True, (180, 180, 180))
            screen.blit(inst_text, (panel_x + 30, inst_y))
            inst_y += 20
