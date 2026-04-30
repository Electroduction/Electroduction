"""
Text-to-Speech System
Converts lesson content to audio for "radio-style" learning
Students can listen to entire lessons being read aloud
"""
from typing import Dict, Any, List
import json
import hashlib
import os

class TextToSpeechSystem:
    """
    Manages text-to-speech functionality for lessons
    Supports multiple voices and speeds
    Caches generated audio files
    """

    def __init__(self):
        self.audio_cache_dir = 'static/audio/lessons'
        os.makedirs(self.audio_cache_dir, exist_ok=True)

        # Voice settings
        self.available_voices = {
            'professional_female': {
                'name': 'Professional Female',
                'language': 'en-US',
                'speed': 1.0,
                'pitch': 1.0
            },
            'professional_male': {
                'name': 'Professional Male',
                'language': 'en-US',
                'speed': 1.0,
                'pitch': 0.9
            },
            'friendly': {
                'name': 'Friendly Instructor',
                'language': 'en-US',
                'speed': 0.95,
                'pitch': 1.05
            }
        }

    def generate_lesson_audio(self, lesson_data: Dict[str, Any],
                            voice_id: str = 'professional_female') -> Dict[str, Any]:
        """
        Generate audio file for entire lesson
        Returns audio file path and metadata
        """
        # Extract all text content from lesson
        full_text = self._compile_lesson_text(lesson_data)

        # Generate unique ID for this audio file
        audio_id = hashlib.md5(
            f"{lesson_data['lesson_id']}{voice_id}{full_text}".encode()
        ).hexdigest()

        audio_file = f"{self.audio_cache_dir}/{audio_id}.mp3"

        # Check if already cached
        if not os.path.exists(audio_file):
            # Generate audio (in production, use actual TTS service)
            self._generate_audio_file(full_text, audio_file, voice_id)

        # Calculate duration
        duration = self._estimate_duration(full_text)

        return {
            'audio_id': audio_id,
            'audio_url': f"/static/audio/lessons/{audio_id}.mp3",
            'duration_seconds': duration,
            'duration_formatted': self._format_duration(duration),
            'voice': self.available_voices[voice_id]['name'],
            'file_size': os.path.getsize(audio_file) if os.path.exists(audio_file) else 0,
            'generated_at': 'cached' if os.path.exists(audio_file) else 'generated'
        }

    def _compile_lesson_text(self, lesson_data: Dict[str, Any]) -> str:
        """Compile all lesson content into readable text"""
        text_parts = []

        # Title
        text_parts.append(f"Lesson: {lesson_data.get('title', 'Untitled')}")
        text_parts.append("\n\n")

        # Learning objectives
        if lesson_data.get('learning_objectives'):
            text_parts.append("Learning Objectives:\n")
            for i, obj in enumerate(lesson_data['learning_objectives'], 1):
                text_parts.append(f"{i}. {obj}\n")
            text_parts.append("\n")

        # Main content
        content = lesson_data.get('content', {})

        if isinstance(content, dict):
            # Introduction
            if content.get('introduction'):
                intro = content['introduction']
                if isinstance(intro, dict):
                    text_parts.append(f"{intro.get('overview', '')}\n\n")
                    text_parts.append(f"{intro.get('importance', '')}\n\n")

            # Core concepts
            if content.get('core_concepts'):
                text_parts.append("Core Concepts:\n\n")
                for i, concept in enumerate(content['core_concepts'], 1):
                    if isinstance(concept, dict):
                        text_parts.append(f"Concept {i}: {concept.get('title', '')}\n")
                        text_parts.append(f"{concept.get('explanation', '')}\n\n")
                    else:
                        text_parts.append(f"{concept}\n\n")

            # Step by step guide
            if content.get('step_by_step_guide'):
                text_parts.append("Step-by-Step Guide:\n\n")
                for i, step in enumerate(content['step_by_step_guide'], 1):
                    if isinstance(step, dict):
                        text_parts.append(f"Step {i}: {step.get('title', '')}\n")
                        text_parts.append(f"{step.get('description', '')}\n\n")
                    else:
                        text_parts.append(f"Step {i}: {step}\n\n")

            # Best practices
            if content.get('best_practices'):
                text_parts.append("Best Practices:\n\n")
                for practice in content['best_practices']:
                    text_parts.append(f"• {practice}\n")
                text_parts.append("\n")

            # Common mistakes
            if content.get('common_mistakes'):
                text_parts.append("Common Mistakes to Avoid:\n\n")
                for mistake in content['common_mistakes']:
                    text_parts.append(f"• {mistake}\n")
                text_parts.append("\n")

            # Summary
            if content.get('summary'):
                text_parts.append("Summary:\n\n")
                text_parts.append(f"{content['summary']}\n\n")

        elif isinstance(content, str):
            text_parts.append(content)

        return ''.join(text_parts)

    def _generate_audio_file(self, text: str, output_file: str, voice_id: str):
        """
        Generate actual audio file using TTS service
        In production, use services like:
        - Google Text-to-Speech
        - Amazon Polly
        - Azure Speech Services
        - ElevenLabs
        """
        # DEMO MODE - In production:
        # from google.cloud import texttospeech
        # client = texttospeech.TextToSpeechClient()
        # synthesis_input = texttospeech.SynthesisInput(text=text)
        # voice = texttospeech.VoiceSelectionParams(
        #     language_code="en-US",
        #     name="en-US-Neural2-F"
        # )
        # audio_config = texttospeech.AudioConfig(
        #     audio_encoding=texttospeech.AudioEncoding.MP3
        # )
        # response = client.synthesize_speech(
        #     input=synthesis_input, voice=voice, audio_config=audio_config
        # )
        # with open(output_file, 'wb') as out:
        #     out.write(response.audio_content)

        # For demo, create placeholder
        with open(output_file, 'w') as f:
            f.write(f"Audio placeholder for: {text[:100]}...")

    def _estimate_duration(self, text: str) -> int:
        """
        Estimate audio duration in seconds
        Average reading speed: ~150 words per minute
        """
        words = len(text.split())
        words_per_second = 150 / 60  # 2.5 words/second
        duration = int(words / words_per_second)
        return duration

    def _format_duration(self, seconds: int) -> str:
        """Format duration as HH:MM:SS"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"

    def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get list of available voices"""
        return [
            {'id': voice_id, **voice_data}
            for voice_id, voice_data in self.available_voices.items()
        ]

    def generate_section_audio(self, section_text: str, section_id: str,
                              voice_id: str = 'professional_female') -> Dict[str, Any]:
        """Generate audio for a specific section of a lesson"""
        audio_id = hashlib.md5(
            f"{section_id}{voice_id}{section_text}".encode()
        ).hexdigest()

        audio_file = f"{self.audio_cache_dir}/section_{audio_id}.mp3"

        if not os.path.exists(audio_file):
            self._generate_audio_file(section_text, audio_file, voice_id)

        duration = self._estimate_duration(section_text)

        return {
            'audio_id': audio_id,
            'audio_url': f"/static/audio/lessons/section_{audio_id}.mp3",
            'duration_seconds': duration,
            'duration_formatted': self._format_duration(duration)
        }

    def get_audio_metadata(self, audio_id: str) -> Dict[str, Any]:
        """Get metadata for a cached audio file"""
        audio_file = f"{self.audio_cache_dir}/{audio_id}.mp3"

        if not os.path.exists(audio_file):
            return {'error': 'Audio file not found'}

        return {
            'audio_id': audio_id,
            'file_size': os.path.getsize(audio_file),
            'exists': True,
            'url': f"/static/audio/lessons/{audio_id}.mp3"
        }

    def generate_playlist(self, program_id: str, lesson_ids: List[str]) -> Dict[str, Any]:
        """Generate playlist for multiple lessons"""
        playlist = {
            'program_id': program_id,
            'lessons': [],
            'total_duration': 0
        }

        # In production, fetch actual lessons and generate audio
        # For demo, create structure
        for lesson_id in lesson_ids:
            lesson_audio = {
                'lesson_id': lesson_id,
                'audio_url': f"/static/audio/lessons/{lesson_id}.mp3",
                'duration': 1500  # 25 minutes
            }
            playlist['lessons'].append(lesson_audio)
            playlist['total_duration'] += lesson_audio['duration']

        playlist['total_duration_formatted'] = self._format_duration(
            playlist['total_duration']
        )

        return playlist

    def clear_cache(self, older_than_days: int = 30):
        """Clear cached audio files older than specified days"""
        import time
        from pathlib import Path

        now = time.time()
        cutoff = now - (older_than_days * 86400)

        cleared_count = 0
        for audio_file in Path(self.audio_cache_dir).glob('*.mp3'):
            if audio_file.stat().st_mtime < cutoff:
                audio_file.unlink()
                cleared_count += 1

        return {
            'cleared_files': cleared_count,
            'message': f'Cleared {cleared_count} audio files older than {older_than_days} days'
        }
