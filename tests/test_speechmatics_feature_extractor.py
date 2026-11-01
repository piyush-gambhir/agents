import numpy as np
import pytest
from speechmatics.voice._smart_turn import SmartTurnDetector
from transformers import WhisperFeatureExtractor

pytestmark = pytest.mark.plugin("speechmatics")


@pytest.mark.asyncio
async def test_smart_turn_feature_extraction_with_patched_transformers(monkeypatch):
    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    detector = SmartTurnDetector(auto_init=False)
    detector.feature_extractor = WhisperFeatureExtractor(chunk_length=8)

    class Session:
        def run(self, outputs, inputs):
            features = inputs["input_features"]
            assert features.shape == (1, 80, 800)
            assert features.dtype == np.float32
            assert np.isfinite(features).all()
            return [np.array([[0.9]], dtype=np.float32)]

    detector.session = Session()
    detector._is_initialized = True
    result = await detector.predict(np.zeros(16000, dtype=np.int16).tobytes(), "en")
    assert result.error is None
    assert result.prediction is True
    assert result.probability == 0.9
