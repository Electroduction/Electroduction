"""
Latent Space Interpolation — Music & Video Generation
DRAFT ALPHA — REQUIRES TESTING AND ITERATION

Blends two database entries in latent space to create new high-quality outputs.
Key for music/video: "Generate a track between lo-fi and jazz" or "Video style between vlog and documentary"

Algorithm: Take embeddings of two known-good entries, interpolate in latent space,
           decode to get a new blended output.

SELF-CORRECTION BLOCK:
    What Could Break:
      1. Embeddings from different models incompatible
      2. Interpolation midpoint falls outside training distribution
      3. Decoded output is "uncanny valley" — technically valid but feels wrong
    How to Test:
      pytest tests/test_latent_interpolation.py -v
    How to Fix:
      Use same embedding model for all database entries
      Add "sanity check" verification after decode
      Store human ratings for interpolated outputs, retrain on good examples
"""

import json
import numpy as np
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Literal


@dataclass
class LatentEntry:
    """A database entry with its latent space embedding."""
    entry_id: str
    domain: str       # "music" | "video"
    metadata: dict    # genre, style, BPM, etc.
    embedding: list[float]  # latent vector
    source_file: str


@dataclass
class InterpolationResult:
    """Result of blending two entries."""
    result_id: str
    source_a: str
    source_b: str
    alpha: float      # blend weight (0.0 = all A, 1.0 = all B)
    embedding: list[float]
    metadata_blend: dict
    created_at: str
    quality_score: Optional[float] = None


EMBEDDINGS_DIR = Path("databases/latent_embeddings")
EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)


class EmbeddingGenerator:
    """
    Generates latent embeddings for database entries.

    In production: Use actual models (CLAP for music, CLIP for video)
    For now: Use metadata-based feature vectors
    """

    def generate_music_embedding(self, metadata: dict) -> list[float]:
        """Generate embedding from music metadata."""
        # Feature vector: [bpm_normalized, genre_vector, mood_vector]
        features = []

        # BPM (normalized to 0-1)
        bpm = metadata.get("bpm", 120)
        features.append(min(bpm / 200.0, 1.0))

        # Genre one-hot (simple version)
        genres = ["lo-fi", "jazz", "edm", "rock", "classical", "hip-hop"]
        genre = metadata.get("genre", "").lower()
        genre_vec = [1.0 if g in genre else 0.0 for g in genres]
        features.extend(genre_vec)

        # Mood vector
        moods = ["calm", "energetic", "dark", "uplifting"]
        mood = metadata.get("mood", "").lower()
        mood_vec = [1.0 if m in mood else 0.0 for m in moods]
        features.extend(mood_vec)

        # Key signature (simplified)
        key = metadata.get("key", "C")
        key_offset = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}.get(key[0], 0)
        features.append(key_offset / 12.0)

        return features

    def generate_video_embedding(self, metadata: dict) -> list[float]:
        """Generate embedding from video metadata."""
        features = []

        # Duration (normalized)
        duration = metadata.get("duration_seconds", 60)
        features.append(min(duration / 600.0, 1.0))  # normalize to 10 min

        # Style one-hot
        styles = ["vlog", "documentary", "tutorial", "short", "cinematic"]
        style = metadata.get("style", "").lower()
        style_vec = [1.0 if s in style else 0.0 for s in styles]
        features.extend(style_vec)

        # Pacing
        pacing = metadata.get("pacing", "medium")
        pacing_map = {"slow": 0.3, "medium": 0.6, "fast": 0.9}
        features.append(pacing_map.get(pacing, 0.6))

        # Color grading
        color = metadata.get("color_grading", "neutral")
        color_map = {"warm": 0.8, "cool": 0.2, "neutral": 0.5, "vibrant": 1.0}
        features.append(color_map.get(color, 0.5))

        return features


class LatentInterpolator:
    """
    Blends two latent entries using spherical linear interpolation (SLERP).

    Why SLERP? Linear interpolation can cause "magnitude collapse" in high-dim spaces.
    SLERP preserves vector magnitude, crucial for decoder stability.
    """

    def __init__(self, domain: Literal["music", "video"]):
        self.domain = domain
        self.generator = EmbeddingGenerator()

    def interpolate(
        self,
        entry_a: LatentEntry,
        entry_b: LatentEntry,
        alpha: float = 0.5,
        method: Literal["slerp", "lerp"] = "slerp",
    ) -> InterpolationResult:
        """
        Blend two latent entries.

        alpha: 0.0 = all A, 0.5 = balanced blend, 1.0 = all B
        method: "slerp" (spherical) or "lerp" (linear)
        """
        vec_a = np.array(entry_a.embedding)
        vec_b = np.array(entry_b.embedding)

        if method == "slerp":
            blended = self._slerp(vec_a, vec_b, alpha)
        else:
            blended = self._lerp(vec_a, vec_b, alpha)

        # Blend metadata
        metadata_blend = self._blend_metadata(entry_a.metadata, entry_b.metadata, alpha)

        result_id = f"{self.domain}_{entry_a.entry_id[:8]}_{entry_b.entry_id[:8]}_alpha{int(alpha*100)}"

        return InterpolationResult(
            result_id=result_id,
            source_a=entry_a.entry_id,
            source_b=entry_b.entry_id,
            alpha=alpha,
            embedding=blended.tolist(),
            metadata_blend=metadata_blend,
            created_at=datetime.utcnow().isoformat(),
        )

    def _slerp(self, v0: np.ndarray, v1: np.ndarray, t: float) -> np.ndarray:
        """Spherical linear interpolation."""
        # Normalize vectors
        v0_norm = v0 / (np.linalg.norm(v0) + 1e-8)
        v1_norm = v1 / (np.linalg.norm(v1) + 1e-8)

        # Compute angle
        dot = np.clip(np.dot(v0_norm, v1_norm), -1.0, 1.0)
        theta = np.arccos(dot)

        # Handle near-parallel vectors
        if theta < 1e-5:
            return self._lerp(v0, v1, t)

        # SLERP formula
        sin_theta = np.sin(theta)
        return (np.sin((1 - t) * theta) / sin_theta) * v0 + (np.sin(t * theta) / sin_theta) * v1

    def _lerp(self, v0: np.ndarray, v1: np.ndarray, t: float) -> np.ndarray:
        """Linear interpolation."""
        return (1 - t) * v0 + t * v1

    def _blend_metadata(self, meta_a: dict, meta_b: dict, alpha: float) -> dict:
        """Blend metadata fields intelligently."""
        blended = {}

        # Numeric fields: interpolate
        for key in ["bpm", "duration_seconds"]:
            if key in meta_a and key in meta_b:
                blended[key] = int((1 - alpha) * meta_a[key] + alpha * meta_b[key])

        # Categorical fields: choose closer one or blend string
        for key in ["genre", "style", "mood"]:
            if key in meta_a and key in meta_b:
                if alpha < 0.5:
                    blended[key] = meta_a[key]
                else:
                    blended[key] = meta_b[key]
                # Add blend notation
                if meta_a[key] != meta_b[key]:
                    blended[key] = f"{meta_a[key]}/{meta_b[key]} blend"

        # Key/color: choose majority
        for key in ["key", "color_grading", "pacing"]:
            if key in meta_a or key in meta_b:
                blended[key] = meta_a.get(key) or meta_b.get(key)

        return blended

    def multi_interpolate(
        self,
        entries: list[LatentEntry],
        weights: Optional[list[float]] = None,
    ) -> InterpolationResult:
        """
        Blend multiple entries with custom weights.

        weights: Must sum to 1.0. If None, equal weights.
        """
        if len(entries) < 2:
            raise ValueError("Need at least 2 entries to interpolate")

        if weights is None:
            weights = [1.0 / len(entries)] * len(entries)

        if len(weights) != len(entries):
            raise ValueError("Weights length must match entries length")

        if abs(sum(weights) - 1.0) > 1e-5:
            raise ValueError("Weights must sum to 1.0")

        # Weighted sum of embeddings
        embeddings = np.array([e.embedding for e in entries])
        weights_arr = np.array(weights).reshape(-1, 1)
        blended = np.sum(embeddings * weights_arr, axis=0)

        # Blend metadata (use first two entries)
        metadata_blend = self._blend_metadata(entries[0].metadata, entries[1].metadata, weights[1])

        result_id = f"{self.domain}_multi_blend_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        return InterpolationResult(
            result_id=result_id,
            source_a=entries[0].entry_id,
            source_b=entries[1].entry_id,
            alpha=weights[1],
            embedding=blended.tolist(),
            metadata_blend=metadata_blend,
            created_at=datetime.utcnow().isoformat(),
        )


class InterpolationDatabase:
    """Stores interpolation results and tracks quality scores."""

    def __init__(self, domain: str):
        self.domain = domain
        self.db_file = EMBEDDINGS_DIR / f"{domain}_interpolations.jsonl"

    def save(self, result: InterpolationResult, quality_score: Optional[float] = None):
        """Save interpolation result with optional quality score."""
        result.quality_score = quality_score
        with open(self.db_file, "a") as f:
            f.write(json.dumps(asdict(result)) + "\n")

    def load_all(self) -> list[InterpolationResult]:
        """Load all interpolation results."""
        if not self.db_file.exists():
            return []
        results = []
        with open(self.db_file) as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    results.append(InterpolationResult(**data))
                except Exception:
                    pass
        return results

    def get_high_quality(self, min_score: float = 0.7) -> list[InterpolationResult]:
        """Return interpolations rated above quality threshold."""
        all_results = self.load_all()
        return [r for r in all_results if r.quality_score and r.quality_score >= min_score]


if __name__ == "__main__":
    # Example: Music interpolation
    gen = EmbeddingGenerator()

    # Entry A: Lo-fi hip-hop
    lofi_meta = {"genre": "lo-fi", "bpm": 80, "mood": "calm", "key": "C"}
    lofi_embedding = gen.generate_music_embedding(lofi_meta)
    lofi = LatentEntry(
        entry_id="lofi_001",
        domain="music",
        metadata=lofi_meta,
        embedding=lofi_embedding,
        source_file="data/music/lofi_001.json",
    )

    # Entry B: Jazz
    jazz_meta = {"genre": "jazz", "bpm": 120, "mood": "uplifting", "key": "F"}
    jazz_embedding = gen.generate_music_embedding(jazz_meta)
    jazz = LatentEntry(
        entry_id="jazz_001",
        domain="music",
        metadata=jazz_meta,
        embedding=jazz_embedding,
        source_file="data/music/jazz_001.json",
    )

    # Interpolate
    interpolator = LatentInterpolator("music")
    result = interpolator.interpolate(lofi, jazz, alpha=0.5, method="slerp")

    print(f"Interpolated result: {result.result_id}")
    print(f"  Blended metadata: {result.metadata_blend}")
    print(f"  Embedding length: {len(result.embedding)}")

    # Save to database
    db = InterpolationDatabase("music")
    db.save(result, quality_score=0.85)
    print(f"\nSaved to {db.db_file}")

    # Example: Multi-interpolation
    edm_meta = {"genre": "edm", "bpm": 140, "mood": "energetic", "key": "G"}
    edm_embedding = gen.generate_music_embedding(edm_meta)
    edm = LatentEntry(
        entry_id="edm_001",
        domain="music",
        metadata=edm_meta,
        embedding=edm_embedding,
        source_file="data/music/edm_001.json",
    )

    multi_result = interpolator.multi_interpolate(
        [lofi, jazz, edm],
        weights=[0.5, 0.3, 0.2],  # 50% lo-fi, 30% jazz, 20% EDM
    )
    print(f"\nMulti-interpolation: {multi_result.metadata_blend}")
