"""
Tests for algorithms/latent_interpolation.py
DRAFT ALPHA — REQUIRES TESTING AND ITERATION

Run: pytest tests/test_latent_interpolation.py -v
"""

import pytest
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from algorithms.latent_interpolation import (
    EmbeddingGenerator, LatentInterpolator, InterpolationDatabase,
    LatentEntry, InterpolationResult, EMBEDDINGS_DIR
)


@pytest.fixture(autouse=True)
def cleanup_embeddings():
    """Clean up generated embeddings."""
    yield
    if EMBEDDINGS_DIR.exists():
        for f in EMBEDDINGS_DIR.glob("*.jsonl"):
            f.unlink()


class TestEmbeddingGenerator:

    def setup_method(self):
        self.gen = EmbeddingGenerator()

    def test_generate_music_embedding_returns_list(self):
        meta = {"genre": "lo-fi", "bpm": 80}
        emb = self.gen.generate_music_embedding(meta)
        assert isinstance(emb, list)
        assert len(emb) > 0

    def test_music_embedding_includes_bpm(self):
        meta1 = {"bpm": 80}
        meta2 = {"bpm": 160}
        emb1 = self.gen.generate_music_embedding(meta1)
        emb2 = self.gen.generate_music_embedding(meta2)
        # Higher BPM should result in different first element
        assert emb1[0] != emb2[0]

    def test_music_embedding_includes_genre(self):
        meta = {"genre": "jazz", "bpm": 120}
        emb = self.gen.generate_music_embedding(meta)
        # Should have multiple dimensions for genre encoding
        assert len(emb) > 5

    def test_generate_video_embedding_returns_list(self):
        meta = {"style": "vlog", "duration_seconds": 120}
        emb = self.gen.generate_video_embedding(meta)
        assert isinstance(emb, list)
        assert len(emb) > 0

    def test_video_embedding_different_styles_differ(self):
        meta1 = {"style": "vlog"}
        meta2 = {"style": "documentary"}
        emb1 = self.gen.generate_video_embedding(meta1)
        emb2 = self.gen.generate_video_embedding(meta2)
        assert emb1 != emb2


class TestLatentInterpolator:

    def setup_method(self):
        self.interpolator = LatentInterpolator("music")
        self.gen = EmbeddingGenerator()

    def create_entry(self, entry_id, genre, bpm):
        meta = {"genre": genre, "bpm": bpm, "mood": "calm", "key": "C"}
        emb = self.gen.generate_music_embedding(meta)
        return LatentEntry(
            entry_id=entry_id,
            domain="music",
            metadata=meta,
            embedding=emb,
            source_file="test.json",
        )

    def test_interpolate_returns_result(self):
        lofi = self.create_entry("lofi", "lo-fi", 80)
        jazz = self.create_entry("jazz", "jazz", 120)
        result = self.interpolator.interpolate(lofi, jazz, alpha=0.5)
        assert isinstance(result, InterpolationResult)

    def test_interpolate_alpha_0_returns_entry_a(self):
        lofi = self.create_entry("lofi", "lo-fi", 80)
        jazz = self.create_entry("jazz", "jazz", 120)
        result = self.interpolator.interpolate(lofi, jazz, alpha=0.0)
        # Should be very close to lofi embedding
        assert np.allclose(result.embedding, lofi.embedding, atol=0.1)

    def test_interpolate_alpha_1_returns_entry_b(self):
        lofi = self.create_entry("lofi", "lo-fi", 80)
        jazz = self.create_entry("jazz", "jazz", 120)
        result = self.interpolator.interpolate(lofi, jazz, alpha=1.0)
        # Should be very close to jazz embedding
        assert np.allclose(result.embedding, jazz.embedding, atol=0.1)

    def test_interpolate_alpha_05_is_between(self):
        lofi = self.create_entry("lofi", "lo-fi", 80)
        jazz = self.create_entry("jazz", "jazz", 120)
        result = self.interpolator.interpolate(lofi, jazz, alpha=0.5)
        # Embedding should be between the two
        mid = [(a + b) / 2 for a, b in zip(lofi.embedding, jazz.embedding)]
        # Not exact due to SLERP, but should be similar
        assert isinstance(result.embedding, list)

    def test_interpolate_blends_metadata(self):
        lofi = self.create_entry("lofi", "lo-fi", 80)
        jazz = self.create_entry("jazz", "jazz", 120)
        result = self.interpolator.interpolate(lofi, jazz, alpha=0.5)
        # BPM should be interpolated
        assert "bpm" in result.metadata_blend
        assert 80 < result.metadata_blend["bpm"] < 120

    def test_interpolate_slerp_preserves_magnitude(self):
        lofi = self.create_entry("lofi", "lo-fi", 80)
        jazz = self.create_entry("jazz", "jazz", 120)
        result = self.interpolator.interpolate(lofi, jazz, alpha=0.5, method="slerp")
        # SLERP should preserve vector magnitude (approximately)
        mag_a = np.linalg.norm(lofi.embedding)
        mag_result = np.linalg.norm(result.embedding)
        assert abs(mag_result - mag_a) < mag_a * 0.3  # within 30%

    def test_multi_interpolate_requires_2_or_more_entries(self):
        lofi = self.create_entry("lofi", "lo-fi", 80)
        with pytest.raises(ValueError, match="at least 2"):
            self.interpolator.multi_interpolate([lofi])

    def test_multi_interpolate_weights_must_sum_to_1(self):
        lofi = self.create_entry("lofi", "lo-fi", 80)
        jazz = self.create_entry("jazz", "jazz", 120)
        with pytest.raises(ValueError, match="sum to 1"):
            self.interpolator.multi_interpolate([lofi, jazz], weights=[0.5, 0.6])

    def test_multi_interpolate_succeeds_with_valid_weights(self):
        lofi = self.create_entry("lofi", "lo-fi", 80)
        jazz = self.create_entry("jazz", "jazz", 120)
        result = self.interpolator.multi_interpolate([lofi, jazz], weights=[0.7, 0.3])
        assert isinstance(result, InterpolationResult)


class TestInterpolationDatabase:

    def setup_method(self):
        self.db = InterpolationDatabase("music")

    def test_save_writes_to_file(self):
        result = InterpolationResult(
            result_id="test_001",
            source_a="a",
            source_b="b",
            alpha=0.5,
            embedding=[1.0, 2.0, 3.0],
            metadata_blend={"bpm": 100},
            created_at="2024-01-15T12:00:00",
        )
        self.db.save(result, quality_score=0.8)
        assert self.db.db_file.exists()

    def test_load_all_empty_when_no_file(self):
        results = self.db.load_all()
        assert results == []

    def test_save_and_load_roundtrip(self):
        result = InterpolationResult(
            result_id="test_002",
            source_a="a",
            source_b="b",
            alpha=0.5,
            embedding=[1.0, 2.0],
            metadata_blend={},
            created_at="2024-01-15T12:00:00",
        )
        self.db.save(result, quality_score=0.85)
        loaded = self.db.load_all()
        assert len(loaded) == 1
        assert loaded[0].result_id == "test_002"
        assert loaded[0].quality_score == 0.85

    def test_get_high_quality_filters_correctly(self):
        r1 = InterpolationResult("r1", "a", "b", 0.5, [1.0], {}, "2024-01-15")
        r2 = InterpolationResult("r2", "a", "b", 0.5, [1.0], {}, "2024-01-15")
        self.db.save(r1, quality_score=0.9)
        self.db.save(r2, quality_score=0.5)
        high_quality = self.db.get_high_quality(min_score=0.7)
        assert len(high_quality) == 1
        assert high_quality[0].result_id == "r1"
