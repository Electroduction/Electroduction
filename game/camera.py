"""
Camera system - Follow player and world-to-screen conversion
"""

import pygame

class Camera:
    """Camera that follows the player"""

    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Camera position (center of view in world space)
        self.x = 0
        self.y = 0

        # Smoothing
        self.follow_speed = 5.0
        self.target_x = 0
        self.target_y = 0

        # Zoom
        self.zoom = 1.0

    def update(self, player):
        """Update camera to follow player smoothly"""
        # Set target to player position
        self.target_x = player.x
        self.target_y = player.y

        # Smooth interpolation
        dx = self.target_x - self.x
        dy = self.target_y - self.y

        self.x += dx * self.follow_speed * 0.1
        self.y += dy * self.follow_speed * 0.1

    def world_to_screen(self, world_x, world_y):
        """Convert world coordinates to screen coordinates"""
        screen_x = (world_x - self.x) * self.zoom + self.screen_width / 2
        screen_y = (world_y - self.y) * self.zoom + self.screen_height / 2
        return screen_x, screen_y

    def screen_to_world(self, screen_x, screen_y):
        """Convert screen coordinates to world coordinates"""
        world_x = (screen_x - self.screen_width / 2) / self.zoom + self.x
        world_y = (screen_y - self.screen_height / 2) / self.zoom + self.y
        return world_x, world_y

    def set_zoom(self, zoom):
        """Set camera zoom level"""
        self.zoom = max(0.5, min(2.0, zoom))
