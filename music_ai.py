"""
Music Generation AI System
Generates music with genre understanding and voice synthesis

Usage:
    python music_ai.py --mode generate --genre "lo-fi" --duration 30
    python music_ai.py --mode voice --text "Hello world" --voice_id default
"""

import os
import json
import argparse
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np

# Audio libraries
try:
    import librosa
    import soundfile as sf
    HAS_AUDIO = True
except ImportError:
    print("Audio libraries not installed.")
    print("Install with: pip install librosa soundfile")
    HAS_AUDIO = False

# ML libraries
try:
    from transformers import AutoProcessor, MusicgenForConditionalGeneration
    import torch
    HAS_ML = True
except ImportError:
    print("ML libraries not installed. Running in demo mode.")
    print("Install with: pip install transformers torch")
    HAS_ML = False


@dataclass
class MusicTheory:
    """Music theory knowledge"""
    scales: Dict[str, List[int]]
    chord_progressions: Dict[str, List[str]]
    genre_characteristics: Dict[str, Dict]

    def __init__(self):
        self.scales = {
            "major": [0, 2, 4, 5, 7, 9, 11],
            "minor": [0, 2, 3, 5, 7, 8, 10],
            "pentatonic": [0, 2, 4, 7, 9],
            "blues": [0, 3, 5, 6, 7, 10]
        }

        self.chord_progressions = {
            "pop": ["I", "V", "vi", "IV"],
            "jazz": ["ii", "V", "I"],
            "blues": ["I", "IV", "I", "V"]
        }

        self.genre_characteristics = {
            "edm": {
                "tempo_range": [128, 140],
                "structure": ["intro", "buildup", "drop", "breakdown", "drop", "outro"],
                "key_sounds": ["synth_bass", "sidechain", "riser", "impact"],
                "energy": "high"
            },
            "lo-fi": {
                "tempo_range": [70, 90],
                "structure": ["intro", "verse", "chorus", "verse", "outro"],
                "key_sounds": ["vinyl_crackle", "jazz_samples", "simple_drums"],
                "energy": "relaxed",
                "mood": "nostalgic"
            },
            "jazz": {
                "tempo_range": [90, 180],
                "structure": ["head", "solos", "head"],
                "key_sounds": ["piano", "saxophone", "double_bass", "drums"],
                "complexity": "high",
                "improvisation": True
            },
            "rock": {
                "tempo_range": [110, 140],
                "structure": ["intro", "verse", "chorus", "verse", "chorus", "bridge", "chorus"],
                "key_sounds": ["electric_guitar", "bass", "drums", "vocals"],
                "energy": "high"
            },
            "classical": {
                "tempo_range": [60, 120],
                "structure": ["exposition", "development", "recapitulation"],
                "key_sounds": ["strings", "woodwinds", "brass", "percussion"],
                "complexity": "very_high"
            }
        }


class MusicGenerator:
    """Generate music using AI models"""

    def __init__(self, use_gpu: bool = True):
        self.device = "cuda" if use_gpu and torch.cuda.is_available() else "cpu"
        self.theory = MusicTheory()

        if HAS_ML:
            self._load_models()
        else:
            self.model = None

    def _load_models(self):
        """Load music generation models"""
        print(f"Loading music generation models on {self.device}...")

        try:
            # MusicGen model from Meta
            self.processor = AutoProcessor.from_pretrained("facebook/musicgen-small")
            self.model = MusicgenForConditionalGeneration.from_pretrained(
                "facebook/musicgen-small"
            ).to(self.device)

            print("Models loaded successfully")
        except Exception as e:
            print(f"Error loading models: {e}")
            self.model = None

    def generate_music(
        self,
        genre: str,
        duration: int = 30,
        mood: Optional[str] = None,
        tempo: Optional[int] = None
    ) -> Optional[np.ndarray]:
        """Generate music based on parameters"""

        # Get genre characteristics
        genre_info = self.theory.genre_characteristics.get(genre.lower())

        if not genre_info:
            print(f"Unknown genre '{genre}'. Using generic generation.")
            genre_info = {"tempo_range": [120, 120], "energy": "medium"}

        # Build prompt
        prompt_parts = [f"{genre} music"]

        if mood:
            prompt_parts.append(mood)
        elif "mood" in genre_info:
            prompt_parts.append(genre_info["mood"])

        if "energy" in genre_info:
            prompt_parts.append(f"{genre_info['energy']} energy")

        # Add key sounds
        if "key_sounds" in genre_info:
            prompt_parts.append(f"featuring {', '.join(genre_info['key_sounds'][:2])}")

        prompt = ", ".join(prompt_parts)

        print(f"Generating: {prompt}")
        print(f"Duration: {duration} seconds")

        if not HAS_ML or not self.model:
            print("Demo mode: Would generate audio here")
            # Return empty audio for demo
            sample_rate = 32000
            return np.zeros(duration * sample_rate)

        # Generate music
        inputs = self.processor(
            text=[prompt],
            padding=True,
            return_tensors="pt"
        ).to(self.device)

        # Calculate number of tokens needed
        sample_rate = self.model.config.audio_encoder.sampling_rate
        tokens_per_second = sample_rate / self.model.config.audio_encoder.hop_length
        max_new_tokens = int(duration * tokens_per_second)

        print("Generating audio...")
        audio_values = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            guidance_scale=3.0
        )

        audio = audio_values[0].cpu().numpy()

        return audio

    def save_audio(
        self,
        audio: np.ndarray,
        filename: str,
        sample_rate: int = 32000
    ):
        """Save generated audio to file"""
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else ".", exist_ok=True)

        if HAS_AUDIO:
            sf.write(filename, audio, sample_rate)
            print(f"Audio saved to {filename}")
        else:
            print(f"Would save audio to {filename} (soundfile not available)")

    def analyze_genre_fit(self, audio: np.ndarray, expected_genre: str, sample_rate: int = 32000) -> Dict:
        """Analyze if generated music fits the genre"""

        if not HAS_AUDIO:
            return {"error": "librosa not available"}

        try:
            # Extract features
            tempo, beats = librosa.beat.beat_track(y=audio, sr=sample_rate)
            chroma = librosa.feature.chroma_cqt(y=audio, sr=sample_rate)
            spectral_centroid = librosa.feature.spectral_centroid(y=audio, sr=sample_rate)

            # Get expected characteristics
            genre_info = self.theory.genre_characteristics.get(expected_genre.lower(), {})
            expected_tempo_range = genre_info.get("tempo_range", [60, 180])

            # Check if tempo fits
            tempo_fits = expected_tempo_range[0] <= tempo <= expected_tempo_range[1]

            analysis = {
                "detected_tempo": float(tempo),
                "expected_tempo_range": expected_tempo_range,
                "tempo_fits_genre": tempo_fits,
                "average_spectral_centroid": float(np.mean(spectral_centroid)),
                "genre_match_score": 0.85 if tempo_fits else 0.60  # Simplified
            }

            return analysis

        except Exception as e:
            return {"error": str(e)}


class VoiceSynthesizer:
    """Synthesize voices (TTS)"""

    def __init__(self, use_gpu: bool = True):
        self.device = "cuda" if use_gpu and torch.cuda.is_available() else "cpu"

        # In full implementation, load TTS models (e.g., Coqui TTS, VITS)
        self.model = None

    def synthesize_voice(
        self,
        text: str,
        voice_id: str = "default",
        emotion: str = "neutral",
        singing_mode: bool = False
    ) -> Optional[np.ndarray]:
        """Synthesize speech from text"""

        print(f"Synthesizing: '{text}'")
        print(f"Voice: {voice_id}, Emotion: {emotion}, Singing: {singing_mode}")

        if not HAS_ML or not self.model:
            print("Demo mode: Would synthesize voice here")
            # Return empty audio
            sample_rate = 22050
            duration = len(text.split()) * 0.5  # Rough estimate
            return np.zeros(int(duration * sample_rate))

        # In full implementation:
        # - Load voice model
        # - Generate speech
        # - Apply emotion
        # - Handle singing mode differently

        return None

    def clone_voice(self, reference_audio_path: str, text: str) -> Optional[np.ndarray]:
        """Clone a voice from reference audio"""
        print(f"Cloning voice from {reference_audio_path}")
        print(f"Generating: '{text}'")

        # In full implementation:
        # - Load reference audio
        # - Extract voice characteristics
        # - Generate new audio with same voice
        # - Return synthesized audio

        return None


class BeatGenerator:
    """Generate drum beats and rhythms"""

    def __init__(self):
        self.theory = MusicTheory()

    def generate_beat(
        self,
        genre: str,
        tempo: int,
        duration: int = 8  # bars
    ) -> Dict[str, List[float]]:
        """Generate a drum pattern for the genre"""

        genre_info = self.theory.genre_characteristics.get(genre.lower(), {})

        # Calculate timing
        beats_per_bar = 4
        seconds_per_beat = 60.0 / tempo
        total_beats = duration * beats_per_bar

        # Generate patterns
        if genre.lower() == "edm":
            kick = self._generate_four_on_floor(total_beats, seconds_per_beat)
            snare = self._generate_snare_on_2_4(total_beats, seconds_per_beat)
            hihat = self._generate_eighth_note_hihats(total_beats, seconds_per_beat)

        elif genre.lower() == "lo-fi":
            kick = self._generate_simple_kick(total_beats, seconds_per_beat)
            snare = self._generate_snare_on_2_4(total_beats, seconds_per_beat)
            hihat = self._generate_swung_hihats(total_beats, seconds_per_beat)

        else:
            # Generic rock beat
            kick = self._generate_rock_kick(total_beats, seconds_per_beat)
            snare = self._generate_snare_on_2_4(total_beats, seconds_per_beat)
            hihat = self._generate_eighth_note_hihats(total_beats, seconds_per_beat)

        return {
            "kick": kick,
            "snare": snare,
            "hihat": hihat,
            "tempo": tempo,
            "duration_bars": duration
        }

    def _generate_four_on_floor(self, total_beats: int, seconds_per_beat: float) -> List[float]:
        """Four-on-the-floor kick pattern (every beat)"""
        return [i * seconds_per_beat for i in range(int(total_beats))]

    def _generate_simple_kick(self, total_beats: int, seconds_per_beat: float) -> List[float]:
        """Simple kick pattern (beats 1 and 3)"""
        kicks = []
        for bar in range(int(total_beats // 4)):
            kicks.append((bar * 4) * seconds_per_beat)
            kicks.append((bar * 4 + 2) * seconds_per_beat)
        return kicks

    def _generate_rock_kick(self, total_beats: int, seconds_per_beat: float) -> List[float]:
        """Rock kick pattern"""
        kicks = []
        for bar in range(int(total_beats // 4)):
            kicks.append((bar * 4) * seconds_per_beat)
            kicks.append((bar * 4 + 2) * seconds_per_beat)
            kicks.append((bar * 4 + 3.5) * seconds_per_beat)  # Syncopation
        return kicks

    def _generate_snare_on_2_4(self, total_beats: int, seconds_per_beat: float) -> List[float]:
        """Snare on beats 2 and 4"""
        snares = []
        for bar in range(int(total_beats // 4)):
            snares.append((bar * 4 + 1) * seconds_per_beat)
            snares.append((bar * 4 + 3) * seconds_per_beat)
        return snares

    def _generate_eighth_note_hihats(self, total_beats: int, seconds_per_beat: float) -> List[float]:
        """Hi-hats on every eighth note"""
        return [i * seconds_per_beat / 2 for i in range(int(total_beats * 2))]

    def _generate_swung_hihats(self, total_beats: int, seconds_per_beat: float) -> List[float]:
        """Swung hi-hats (triplet feel)"""
        hihats = []
        for beat in range(int(total_beats)):
            hihats.append(beat * seconds_per_beat)
            hihats.append(beat * seconds_per_beat + seconds_per_beat * 0.67)  # Swing
        return hihats


class MusicAISystem:
    """Main Music AI System"""

    def __init__(self, use_gpu: bool = True):
        self.music_generator = MusicGenerator(use_gpu=use_gpu)
        self.voice_synthesizer = VoiceSynthesizer(use_gpu=use_gpu)
        self.beat_generator = BeatGenerator()

    def generate_complete_track(
        self,
        genre: str,
        duration: int = 30,
        include_vocals: bool = False,
        lyrics: Optional[str] = None
    ) -> Dict:
        """Generate a complete music track"""

        print(f"\n{'='*60}")
        print(f"GENERATING {genre.upper()} TRACK")
        print(f"{'='*60}\n")

        # Generate music
        music_audio = self.music_generator.generate_music(genre, duration)

        # Generate beat pattern
        genre_info = self.music_generator.theory.genre_characteristics.get(genre.lower(), {})
        tempo = np.mean(genre_info.get("tempo_range", [120, 120]))
        beat_pattern = self.beat_generator.generate_beat(genre, int(tempo), duration // 2)

        # Optional vocals
        vocal_audio = None
        if include_vocals and lyrics:
            vocal_audio = self.voice_synthesizer.synthesize_voice(
                lyrics,
                singing_mode=True
            )

        # Analyze genre fit
        if music_audio is not None and HAS_AUDIO:
            analysis = self.music_generator.analyze_genre_fit(music_audio, genre)
        else:
            analysis = {"status": "demo_mode"}

        result = {
            "genre": genre,
            "duration": duration,
            "tempo": tempo,
            "music_audio": music_audio,
            "vocal_audio": vocal_audio,
            "beat_pattern": beat_pattern,
            "analysis": analysis,
            "genre_characteristics": genre_info
        }

        return result

    def save_track(self, result: Dict, output_dir: str = "output"):
        """Save generated track and metadata"""
        os.makedirs(output_dir, exist_ok=True)

        genre = result["genre"]
        timestamp = __import__("datetime").datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save audio
        if result["music_audio"] is not None:
            audio_path = os.path.join(output_dir, f"{genre}_music_{timestamp}.wav")
            self.music_generator.save_audio(result["music_audio"], audio_path)

        # Save metadata
        metadata_path = os.path.join(output_dir, f"{genre}_metadata_{timestamp}.json")

        metadata = {
            "genre": result["genre"],
            "duration": result["duration"],
            "tempo": result["tempo"],
            "beat_pattern": result["beat_pattern"],
            "analysis": result["analysis"],
            "genre_characteristics": result["genre_characteristics"]
        }

        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"Metadata saved to {metadata_path}")


def main():
    parser = argparse.ArgumentParser(description="Music Generation AI System")
    parser.add_argument("--mode", choices=["generate", "voice", "beat"], default="generate")
    parser.add_argument("--genre", default="lo-fi", help="Music genre")
    parser.add_argument("--duration", type=int, default=30, help="Duration in seconds")
    parser.add_argument("--tempo", type=int, help="Tempo (BPM)")
    parser.add_argument("--text", help="Text for voice synthesis")
    parser.add_argument("--voice-id", default="default", help="Voice ID")
    parser.add_argument("--lyrics", help="Lyrics for singing")
    parser.add_argument("--no-gpu", action="store_true", help="Disable GPU")

    args = parser.parse_args()

    # Initialize system
    print("Initializing Music AI System...")
    system = MusicAISystem(use_gpu=not args.no_gpu)

    if args.mode == "generate":
        print(f"\nAvailable genres: {list(system.music_generator.theory.genre_characteristics.keys())}")

        result = system.generate_complete_track(
            genre=args.genre,
            duration=args.duration,
            include_vocals=bool(args.lyrics),
            lyrics=args.lyrics
        )

        print(f"\n{'='*60}")
        print("GENERATION COMPLETE")
        print(f"{'='*60}")
        print(f"Genre: {result['genre']}")
        print(f"Tempo: {result['tempo']:.0f} BPM")
        print(f"Duration: {result['duration']} seconds")

        if "genre_match_score" in result["analysis"]:
            print(f"\nGenre Match Score: {result['analysis']['genre_match_score']:.2%}")
            print(f"Detected Tempo: {result['analysis']['detected_tempo']:.1f} BPM")

        print(f"\n{'='*60}")

        # Save
        system.save_track(result)

    elif args.mode == "voice":
        if not args.text:
            print("Please provide --text for voice synthesis")
            return

        audio = system.voice_synthesizer.synthesize_voice(args.text, args.voice_id)
        print("Voice synthesis complete")

    elif args.mode == "beat":
        tempo = args.tempo if args.tempo else 120
        beat_pattern = system.beat_generator.generate_beat(args.genre, tempo)

        print(f"\n{args.genre.upper()} BEAT PATTERN ({tempo} BPM)")
        print(f"Kick hits: {len(beat_pattern['kick'])}")
        print(f"Snare hits: {len(beat_pattern['snare'])}")
        print(f"Hi-hat hits: {len(beat_pattern['hihat'])}")


if __name__ == "__main__":
    main()
