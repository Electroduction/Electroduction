"""
Audio System - Music and sound effects using procedural generation
"""

import pygame
import math
import random
import numpy as np

class AudioSystem:
    """Manages music and sound effects"""

    def __init__(self):
        # Initialize pygame mixer
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

        # Sound channels
        self.music_channel = None
        self.sfx_channels = []

        # Volume
        self.music_volume = 0.3
        self.sfx_volume = 0.5

        # Cache
        self.sound_cache = {}

        print("Audio system initialized")

    def generate_tone(self, frequency, duration, volume=0.5, wave_type='sine'):
        """Generate a simple tone"""
        sample_rate = 22050
        num_samples = int(sample_rate * duration)

        # Generate samples
        samples = []
        for i in range(num_samples):
            t = i / sample_rate

            if wave_type == 'sine':
                value = math.sin(2 * math.pi * frequency * t)
            elif wave_type == 'square':
                value = 1 if math.sin(2 * math.pi * frequency * t) > 0 else -1
            elif wave_type == 'sawtooth':
                value = 2 * (t * frequency - math.floor(t * frequency + 0.5))
            else:
                value = 0

            # Apply envelope (fade in/out)
            envelope = 1.0
            fade_duration = min(0.05, duration / 4)

            if t < fade_duration:
                envelope = t / fade_duration
            elif t > duration - fade_duration:
                envelope = (duration - t) / fade_duration

            samples.append(int(value * volume * envelope * 32767))

        # Convert to stereo
        stereo_samples = [(s, s) for s in samples]

        # Create sound
        sound_array = np.array(stereo_samples, dtype=np.int16)
        sound = pygame.sndarray.make_sound(sound_array)

        return sound

    def play_attack_sound(self):
        """Play attack sound"""
        if 'attack' not in self.sound_cache:
            # Generate swoosh sound
            sound = self.generate_tone(200, 0.1, self.sfx_volume, 'sawtooth')
            self.sound_cache['attack'] = sound

        self.sound_cache['attack'].play()

    def play_hit_sound(self):
        """Play hit/damage sound"""
        if 'hit' not in self.sound_cache:
            # Generate impact sound
            sound = self.generate_tone(150, 0.08, self.sfx_volume, 'square')
            self.sound_cache['hit'] = sound

        self.sound_cache['hit'].play()

    def play_death_sound(self):
        """Play enemy death sound"""
        if 'death' not in self.sound_cache:
            # Descending tone
            sound = self.generate_tone(300, 0.3, self.sfx_volume * 0.8, 'sine')
            self.sound_cache['death'] = sound

        self.sound_cache['death'].play()

    def play_level_up_sound(self):
        """Play level up sound"""
        if 'levelup' not in self.sound_cache:
            # Ascending arpeggio
            sound = self.generate_tone(440, 0.2, self.sfx_volume, 'sine')
            self.sound_cache['levelup'] = sound

        self.sound_cache['levelup'].play()

    def play_pickup_sound(self):
        """Play item pickup sound"""
        if 'pickup' not in self.sound_cache:
            sound = self.generate_tone(600, 0.1, self.sfx_volume, 'sine')
            self.sound_cache['pickup'] = sound

        self.sound_cache['pickup'].play()

    def play_ability_sound(self):
        """Play ability cast sound"""
        if 'ability' not in self.sound_cache:
            sound = self.generate_tone(500, 0.15, self.sfx_volume, 'square')
            self.sound_cache['ability'] = sound

        self.sound_cache['ability'].play()

    def play_shop_sound(self):
        """Play shop transaction sound"""
        if 'shop' not in self.sound_cache:
            sound = self.generate_tone(550, 0.12, self.sfx_volume, 'sine')
            self.sound_cache['shop'] = sound

        self.sound_cache['shop'].play()

    def play_menu_sound(self):
        """Play menu navigation sound"""
        if 'menu' not in self.sound_cache:
            sound = self.generate_tone(400, 0.05, self.sfx_volume * 0.6, 'sine')
            self.sound_cache['menu'] = sound

        self.sound_cache['menu'].play()

    def set_music_volume(self, volume):
        """Set music volume"""
        self.music_volume = max(0.0, min(1.0, volume))
        if self.music_channel:
            self.music_channel.set_volume(self.music_volume)

    def set_sfx_volume(self, volume):
        """Set SFX volume"""
        self.sfx_volume = max(0.0, min(1.0, volume))

    def stop_all(self):
        """Stop all audio"""
        pygame.mixer.stop()

# Global audio system instance
_audio_system = None

def get_audio_system():
    """Get global audio system"""
    global _audio_system
    if _audio_system is None:
        try:
            _audio_system = AudioSystem()
        except:
            # Fallback if audio fails
            print("Warning: Audio system failed to initialize")
            _audio_system = type('DummyAudio', (), {
                'play_attack_sound': lambda: None,
                'play_hit_sound': lambda: None,
                'play_death_sound': lambda: None,
                'play_level_up_sound': lambda: None,
                'play_pickup_sound': lambda: None,
                'play_ability_sound': lambda: None,
                'play_shop_sound': lambda: None,
                'play_menu_sound': lambda: None,
                'set_music_volume': lambda v: None,
                'set_sfx_volume': lambda v: None,
                'stop_all': lambda: None
            })()

    return _audio_system
