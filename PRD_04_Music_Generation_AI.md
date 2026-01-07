# PRD: AI Music Generation & Voice Synthesis System

## Executive Summary
Create an AI system that understands music fundamentals, generates genre-specific music, and synthesizes voices by training on large audio datasets with deep understanding of what makes "good" music.

## Research Phase Findings

### Key Music Datasets

#### Large-Scale Music Datasets
1. **Free Music Archive (FMA)**
   - 106,574 tracks, 30-second clips
   - 161 genres
   - Full metadata (artist, album, genre, tags)
   - Use: Genre classification and generation baseline

2. **Million Song Dataset**
   - 1 million contemporary tracks
   - Audio features + metadata
   - No audio files (features only)
   - Use: Large-scale music understanding

3. **MAESTRO Dataset (Google)**
   - 200 hours of piano performances
   - MIDI + audio aligned
   - Professional quality
   - Use: Classical music generation, timing

4. **Lakh MIDI Dataset**
   - 176,581 MIDI files
   - Genre tags, metadata
   - Use: Symbolic music generation

5. **MusicNet**
   - 330 recordings of classical music
   - Note-level annotations
   - Use: Music theory training

6. **NSynth Dataset (Google)**
   - 300,000+ musical notes
   - 1,000 instruments
   - 4 seconds each
   - Use: Instrument synthesis, timbre learning

7. **AudioSet (YouTube-8M Audio)**
   - 2 million YouTube clips
   - 632 audio classes (includes music)
   - Use: Audio understanding

#### Voice/Speech Datasets
8. **VCTK Corpus**
   - 110 English speakers
   - 400+ utterances each
   - Multiple accents
   - Use: Voice characteristics learning

9. **LibriSpeech**
   - 1,000 hours of English audiobooks
   - Clean audio
   - Use: Speech patterns

10. **Common Voice (Mozilla)**
    - 18,000+ hours
    - Multiple languages
    - Diverse speakers
    - Use: Voice diversity training

11. **VIMAS (Singing Voice)**
    - Singing voice dataset
    - Multiple genres
    - Use: Singing synthesis

#### Music Theory & Analysis
12. **Hooktheory Database**
    - Chord progressions from popular songs
    - Theory annotations
    - Use: Learn popular music patterns

13. **McGill Billboard Dataset**
    - Chord annotations for Billboard hits
    - Structure analysis
    - Use: Hit song patterns

14. **MUSDB18**
    - 150 full songs
    - Separated stems (vocals, drums, bass, other)
    - Use: Mixing, stem generation

### Why Our Fine-Tuned Data Will Be Better

1. **Multi-Modal Training**: Combine audio + MIDI + music theory simultaneously
2. **Genre Expertise**: Separate models per genre with genre-specific features
3. **Music Theory Integration**: Not just patterns, but WHY progressions work
4. **Quality Filtering**: Train only on high-rated music (>4 stars)
5. **Timing and Feel**: Capture micro-timing, swing, groove (not just quantized MIDI)
6. **Emotional Context**: Label music with emotions and use cases
7. **Hierarchical Structure**: Understand intro, verse, chorus, bridge patterns
8. **Voice-Music Integration**: Train voices with backing tracks for naturalness

## System Architecture

### Multi-Stage Generation Pipeline

```
User Input (Description) → Genre Classifier → Music Generator →
Arrangement Engine → Mixing/Mastering → Quality Check → Output
```

### Voice + Music Integration

```
Lyrics → Voice Synthesizer ↘
                           → Timing Coordinator → Mixed Output
Music → Beat Generator    ↗
```

## Technical Approach

### 1. Music Generation Models

**Architecture Options**:
- **MusicGen (Meta)**: Text-to-music generation (base model)
- **AudioLDM**: Audio diffusion model
- **Jukebox (OpenAI)**: High-quality but computationally expensive
- **MuseNet**: Symbolic music generation
- **Custom Transformer**: Trained on our curated dataset

**Our Approach**: Fine-tune MusicGen + Custom genre-specific models

### 2. Music Theory Engine

```python
music_theory_knowledge = {
    "scales": {
        "major": [0, 2, 4, 5, 7, 9, 11],
        "minor": [0, 2, 3, 5, 7, 8, 10],
        "pentatonic": [0, 2, 4, 7, 9],
        # ... all scales
    },
    "chord_progressions": {
        "pop": ["I-V-vi-IV", "I-IV-V", "vi-IV-I-V"],
        "jazz": ["ii-V-I", "I-vi-ii-V"],
        "blues": ["I-I-I-I-IV-IV-I-I-V-IV-I-V"]
    },
    "genre_characteristics": {
        "edm": {
            "tempo": [128, 140],
            "structure": ["intro", "buildup", "drop", "breakdown", "drop", "outro"],
            "key_sounds": ["synth_bass", "sidechain", "riser", "impact"]
        },
        "jazz": {
            "tempo": [90, 180],
            "complexity": "high",
            "improvisation": True,
            "chord_extensions": ["7th", "9th", "11th", "13th"]
        },
        "lo-fi_hip_hop": {
            "tempo": [70, 90],
            "characteristics": ["vinyl_crackle", "jazz_samples", "simple_drums"],
            "mood": "relaxed"
        }
    }
}
```

### 3. Genre-Specific Models

Train specialized models for major genres:
- **EDM/Electronic**: Focus on synthesis, build-ups, drops
- **Hip-Hop**: Beat patterns, sampling, flow
- **Jazz**: Complex harmonies, improvisation
- **Classical**: Orchestration, counterpoint
- **Rock**: Guitar patterns, song structure
- **Lo-fi**: Texture, mood, simplicity

### 4. Voice Synthesis

**Base Models**:
- **VITS**: End-to-end TTS
- **Bark**: Generative audio model
- **Tortoise TTS**: High-quality but slow
- **Coqui TTS**: Fast and customizable

**Training Approach**:
```python
voice_training_pipeline = {
    "data_collection": "10+ hours per voice",
    "preprocessing": "noise reduction, normalization",
    "fine_tuning": "VITS model on speaker data",
    "multi_speaker": "Combine multiple voices for variety",
    "emotion_control": "Add emotional prosody",
    "singing_mode": "Separate training for singing vs. speaking"
}
```

### 5. What Makes "Good" Music?

**Quantifiable Factors**:
```python
quality_metrics = {
    "technical": {
        "mix_balance": "Frequency distribution",
        "dynamic_range": "Not over-compressed",
        "harmonic_content": "Rich harmonics",
        "timing_precision": "Groove and feel"
    },
    "musical": {
        "melody_memorability": "Repetition + variation balance",
        "harmonic_interest": "Tension and resolution",
        "rhythmic_drive": "Groove consistency",
        "structural_flow": "Intro → build → climax → resolution"
    },
    "genre_fit": {
        "style_consistency": "Matches genre expectations",
        "innovation": "Unique but not alienating",
        "production_quality": "Professional sound"
    },
    "emotional": {
        "mood_clarity": "Clear emotional message",
        "engagement": "Holds listener attention",
        "satisfaction": "Fulfilling experience"
    }
}
```

**Training on Quality**:
- Use only 4+ star rated music
- Train quality predictor on user ratings
- Incorporate music theory correctness
- A/B test generations with listeners

### 6. Beat and Sound Generation

```python
class BeatGenerator:
    def generate_beat(self, genre, tempo, mood):
        # Load genre template
        template = self.genre_templates[genre]

        # Generate drum pattern
        kick = self.generate_kick_pattern(tempo, template)
        snare = self.generate_snare_pattern(tempo, template)
        hihat = self.generate_hihat_pattern(tempo, template)

        # Add genre-specific elements
        if genre == "trap":
            hihats = self.add_hihat_rolls(hihat)
            add_808_slides(kick)
        elif genre == "jazz":
            add_swing(kick, snare, hihat)
            add_brush_variations(snare)

        # Synthesize
        beat = self.synthesize_drums(kick, snare, hihat)

        return beat

class MelodyGenerator:
    def generate_melody(self, key, scale, chord_progression, genre):
        # Get scale notes
        scale_notes = self.get_scale_notes(key, scale)

        # Generate contour
        contour = self.generate_melodic_contour()

        # Fit to chord progression
        notes = self.fit_to_chords(contour, chord_progression, scale_notes)

        # Add genre-specific ornaments
        notes = self.add_genre_characteristics(notes, genre)

        # Rhythm
        rhythm = self.generate_rhythm(genre)

        return self.combine_pitch_rhythm(notes, rhythm)
```

## Implementation Steps

### Phase 1: Data Collection (Weeks 1-3)

```bash
# Download FMA
wget https://os.unil.cloud.switch.ch/fma/fma_large.zip
unzip fma_large.zip

# Download MAESTRO
wget https://storage.googleapis.com/magentadata/datasets/maestro/v3.0.0/maestro-v3.0.0.zip

# Download VCTK
wget https://datashare.ed.ac.uk/download/DS_10283_3443.zip

# Clone Lakh MIDI
git clone https://github.com/craffel/lmd

# NSynth (requires gsutil)
gsutil -m cp -r gs://magentadata/datasets/nsynth/nsynth-train.jsonwav.tar.gz .
```

**Manual Collection**:
1. Scrape Freesound.org for effects and instruments
2. YouTube audio downloads (with permission/legal sources only)
3. Hooktheory database access
4. Billboard chord annotations

### Phase 2: Data Processing (Weeks 4-5)

1. **Audio Preprocessing**
   ```python
   # Standardize format
   - Convert to 44.1kHz, stereo
   - Normalize loudness to -14 LUFS
   - Trim silence
   - Extract 30-second clips
   ```

2. **Feature Extraction**
   - MFCCs (Mel-frequency cepstral coefficients)
   - Chroma features
   - Tempo and beat tracking
   - Key detection
   - Genre classification features

3. **Music Theory Annotation**
   ```python
   for song in dataset:
       song.key = detect_key(song.audio)
       song.tempo = detect_tempo(song.audio)
       song.chords = extract_chords(song.audio)
       song.structure = analyze_structure(song.audio)
       song.mood = classify_mood(song.audio)
   ```

4. **Quality Filtering**
   - Remove low-quality recordings
   - Filter by user ratings
   - Remove duplicates
   - Balance genre distribution

5. **Voice Data Processing**
   - Speaker diarization
   - Emotion labeling
   - Phoneme alignment
   - Pitch and formant analysis

### Phase 3: Model Training (Weeks 6-12)

**Week 6-7: Base Music Generator**
```python
# Fine-tune MusicGen
model = MusicGen.from_pretrained("facebook/musicgen-medium")
model.fine_tune(
    dataset=processed_fma,
    epochs=50,
    batch_size=16,
    learning_rate=1e-5
)
```

**Week 8: Genre-Specific Models**
```python
for genre in ["edm", "jazz", "hip-hop", "classical"]:
    genre_model = clone_base_model()
    genre_data = filter_by_genre(dataset, genre)
    genre_model.fine_tune(genre_data)
    save_model(f"musicgen_{genre}")
```

**Week 9: Music Theory Integration**
```python
# Train theory-aware model
theory_model = TheoryGuidedGenerator(
    base_model=musicgen,
    theory_rules=music_theory_knowledge
)
theory_model.train(
    music_data=processed_fma,
    theory_annotations=chord_progressions
)
```

**Week 10-11: Voice Synthesis**
```python
# Fine-tune VITS for multiple voices
for speaker in voice_dataset.speakers:
    voice_model = VITS()
    speaker_data = voice_dataset.filter(speaker)
    voice_model.fine_tune(speaker_data, epochs=1000)
    save_model(f"voice_{speaker.id}")

# Train singing voice separately
singing_model = SingingVoiceSynthesis()
singing_model.train(vimas_dataset)
```

**Week 12: Integration & Quality Model**
```python
# Train quality predictor
quality_model = QualityPredictor()
quality_model.train(
    music_samples=generated_samples,
    human_ratings=crowdsourced_ratings
)

# Reject low-quality outputs
def generate_with_quality_check(prompt, genre):
    for attempt in range(5):
        sample = music_generator.generate(prompt, genre)
        quality = quality_model.predict(sample)
        if quality > 0.7:
            return sample
    return best_sample
```

### Phase 4: System Development (Weeks 13-16)

1. **API Development**
   ```python
   @app.post("/generate/music")
   def generate_music(
       prompt: str,
       genre: str,
       duration: int = 60,
       mood: str = None,
       tempo: int = None
   ):
       music = music_generator.generate(
           prompt=prompt,
           genre=genre,
           duration=duration,
           mood=mood,
           tempo=tempo
       )
       return {"audio_url": upload_to_storage(music)}

   @app.post("/generate/voice")
   def generate_voice(
       text: str,
       voice_id: str,
       emotion: str = "neutral",
       singing: bool = False
   ):
       voice = voice_synthesizer.synthesize(
           text=text,
           voice_id=voice_id,
           emotion=emotion,
           singing_mode=singing
       )
       return {"audio_url": upload_to_storage(voice)}
   ```

2. **Web Interface**
   - Music generation controls (genre, mood, tempo, etc.)
   - Real-time generation
   - Stem editing (adjust individual instruments)
   - Voice cloning interface
   - Mixing tools

3. **DAW Plugin** (Optional)
   - VST/AU plugin for FL Studio, Ableton, Logic
   - Generate music within DAW
   - MIDI export

### Phase 5: Testing (Weeks 17-18)

1. **Music Quality Tests**
   - Blind listening tests vs. human-composed music
   - Genre classification accuracy
   - Music theory correctness
   - Professional producer evaluation

2. **Voice Quality Tests**
   - MOS (Mean Opinion Score) for naturalness
   - WER (Word Error Rate) for intelligibility
   - Speaker similarity (cosine distance in embedding space)
   - Emotional expressiveness rating

3. **Comparative Benchmarks**
   - vs. MusicGen (base model)
   - vs. Suno, Udio (commercial music AI)
   - vs. Eleven Labs (voice AI)
   - vs. Human composers/singers

4. **Technical Metrics**
   - FAD Score (Fréchet Audio Distance)
   - KL Divergence (genre distribution)
   - Pitch accuracy (for voices)
   - Rhythmic precision

## Evaluation Metrics

### Music Generation
- **FAD Score**: Lower is better (distance from real music)
- **Genre Classification**: Generated music classified correctly
- **Music Theory Validity**: Chord progressions make sense
- **Human Preference**: Blind A/B tests
- **Memorability**: Can listeners recall melody?
- **Danceability** (for rhythmic genres): Groove rating

### Voice Synthesis
- **MOS Score**: 1-5 scale, target >4.0
- **Speaker Similarity**: Embedding distance, target >0.9
- **Intelligibility**: WER, target <5%
- **Emotional Accuracy**: Emotion classification of output
- **Naturalness**: Human-like prosody rating

### System Performance
- **Generation Speed**: Real-time factor (RTF < 1.0 ideal)
- **Memory Usage**: GPU/CPU requirements
- **Quality Consistency**: Stddev of quality scores
- **Customization Range**: How well it follows parameters

## Unique Features

1. **Genre Expertise**: Deep understanding of genre conventions
2. **Music Theory Grounding**: Generates theoretically sound music
3. **Voice-Music Sync**: Coordinated voice + beat generation
4. **Stem Separation**: Generate and edit individual instruments
5. **Quality Guarantee**: Reject bad outputs automatically
6. **Emotional Control**: Fine-grained mood and emotion
7. **Interactive Editing**: Modify generated music iteratively
8. **MIDI Export**: Use in DAWs for further production

## Risk Mitigation

1. **Copyright**: Only train on permissively licensed music
2. **Voice Cloning Ethics**: Require consent for voice cloning
3. **Quality Control**: Multiple validation stages
4. **Overfitting**: Ensure diversity in outputs
5. **Bias**: Balance genre and cultural representation

## Success Criteria

1. **Music Quality**: 70% preference over base MusicGen in blind tests
2. **Genre Accuracy**: 90%+ correct genre classification
3. **Voice MOS**: >4.0 naturalness score
4. **Generation Speed**: <30 seconds for 1 minute of music
5. **Theory Correctness**: 95%+ valid chord progressions
6. **User Satisfaction**: 4.5+ stars average
7. **Commercial Viability**: Used by 100+ musicians/producers

## Tools & Frameworks

- **Audio Processing**: librosa, torchaudio, pydub
- **Music Generation**: MusicGen, AudioLDM, Magenta
- **Voice Synthesis**: Coqui TTS, VITS, Bark
- **Music Theory**: music21, mingus
- **ML**: PyTorch, Transformers
- **DAW Integration**: JUCE framework (for VST/AU)

## Dataset Access & Next Steps

### Immediate Actions (Human Can Start)

1. **Download Datasets**
   ```bash
   # Install dependencies
   pip install librosa torch torchaudio pydub music21

   # FMA
   wget https://os.unil.cloud.switch.ch/fma/fma_small.zip  # Start with small

   # MAESTRO
   wget https://storage.googleapis.com/magentadata/datasets/maestro/v3.0.0/maestro-v3.0.0-midi.zip

   # Create directory structure
   mkdir -p data/{music,voice,midi,processed}
   ```

2. **Setup Audio Processing**
   ```python
   import librosa
   import numpy as np

   # Test audio loading
   audio, sr = librosa.load("test_song.mp3", sr=44100)
   tempo, beats = librosa.beat.beat_track(y=audio, sr=sr)
   chroma = librosa.feature.chroma_cqt(y=audio, sr=sr)
   ```

3. **Access Music Theory Resources**
   - Hooktheory: https://www.hooktheory.com/theorytab
   - Billboard Chord Dataset: ddmal.music.mcgill.ca/research/The_McGill_Billboard_Project

4. **Voice Dataset Access**
   - VCTK: https://datashare.ed.ac.uk/handle/10283/3443
   - Common Voice: https://commonvoice.mozilla.org/en/datasets

### Development Setup
```bash
git clone <repo>
cd music-ai
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Download initial datasets
python scripts/download_datasets.py --datasets fma,maestro,vctk

# Test audio processing
python tests/test_audio_pipeline.py
```

## Future Enhancements

1. **Real-Time Collaboration**: Multiple users generate together
2. **Music Video Sync**: Generate visuals synced to music
3. **Live Performance Mode**: Real-time generation during performances
4. **Genre Fusion**: Mix multiple genres intelligently
5. **Mastering AI**: Automatic professional mastering
6. **Lyrics Generation**: Complete songs with generated lyrics
7. **Music Education**: Teach music theory through generation
