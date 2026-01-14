"""Unit tests for PlaceholderAudioService."""

import io
import wave
from unittest.mock import MagicMock, patch

import pytest

from adapter.audio.placeholder_audio_service import PlaceholderAudioService


class TestPlaceholderAudioService:
    """Test cases for PlaceholderAudioService."""

    def test_init_default_multiplier(self):
        """Test initialization with default multiplier."""
        service = PlaceholderAudioService()
        assert service.silence_duration_multiplier == 0.4

    def test_init_custom_multiplier(self):
        """Test initialization with custom multiplier."""
        service = PlaceholderAudioService(silence_duration_multiplier=0.5)
        assert service.silence_duration_multiplier == 0.5

    @pytest.mark.asyncio
    async def test_get_audio_for_theme_with_duration(self):
        """Test get_audio_for_theme with explicit duration."""
        service = PlaceholderAudioService()

        with patch.object(service, "_generate_silence_wav") as mock_generate:
            mock_generate.return_value = b"fake_wav_data"

            result = await service.get_audio_for_theme(
                "test theme", duration_seconds=10
            )

            mock_generate.assert_called_once_with(10)
            assert result == b"fake_wav_data"

    @pytest.mark.asyncio
    async def test_get_audio_for_theme_without_duration(self):
        """Test get_audio_for_theme without duration (estimation)."""
        service = PlaceholderAudioService(silence_duration_multiplier=0.5)

        with patch.object(service, "_generate_silence_wav") as mock_generate:
            mock_generate.return_value = b"fake_wav_data"

            # "hello world test" has 3 words, 3 * 0.5 = 1.5, clamped to 5
            result = await service.get_audio_for_theme("hello world test")

            mock_generate.assert_called_once_with(5)
            assert result == b"fake_wav_data"

    @pytest.mark.asyncio
    async def test_get_audio_for_theme_duration_estimation_clamp_max(self):
        """Test duration estimation clamps to maximum."""
        service = PlaceholderAudioService(
            silence_duration_multiplier=20.0
        )  # High multiplier

        with patch.object(service, "_generate_silence_wav") as mock_generate:
            mock_generate.return_value = b"fake_wav_data"

            # Many words to exceed 60 seconds
            long_theme = "word " * 100  # 100 words
            result = await service.get_audio_for_theme(long_theme)

            mock_generate.assert_called_once_with(60)  # Clamped to 60
            assert result == b"fake_wav_data"

    @pytest.mark.asyncio
    async def test_get_audio_for_theme_duration_estimation_clamp_min(self):
        """Test duration estimation clamps to minimum."""
        service = PlaceholderAudioService(
            silence_duration_multiplier=0.1
        )  # Low multiplier

        with patch.object(service, "_generate_silence_wav") as mock_generate:
            mock_generate.return_value = b"fake_wav_data"

            # Few words to get below 5 seconds
            short_theme = "hi"
            result = await service.get_audio_for_theme(short_theme)

            mock_generate.assert_called_once_with(5)  # Clamped to 5
            assert result == b"fake_wav_data"

    @pytest.mark.asyncio
    async def test_get_audio_metadata_mp3(self):
        """Test metadata extraction for MP3 files."""
        service = PlaceholderAudioService()

        # Mock MP3 data
        mock_mp3 = MagicMock()
        mock_mp3.info.bitrate = 128000
        mock_mp3.info.bitrate_mode = "CBR"

        mock_audio_segment = MagicMock()
        mock_audio_segment.channels = 2
        mock_audio_segment.frame_rate = 44100
        mock_audio_segment.sample_width = 2
        mock_audio_segment.__len__ = MagicMock(return_value=30000)  # 30 seconds in ms

        mp3_data = b"ID3\x00\x00\x00\x00\x00\x00"  # Fake MP3 header

        with patch(
            "pydub.AudioSegment.from_file", return_value=mock_audio_segment
        ), patch("adapter.audio.placeholder_audio_service.MP3", return_value=mock_mp3):

            result = await service.get_audio_metadata(mp3_data)

            assert result["duration_seconds"] == 30.0
            assert result["channels"] == 2
            assert result["sample_rate"] == 44100
            assert result["sample_width"] == 2
            assert result["size_bytes"] == len(mp3_data)
            assert result["format"] == "mp3"
            assert result["bitrate"] == 128000
            assert result["bitrate_mode"] == "CBR"

    @pytest.mark.asyncio
    async def test_get_audio_metadata_wav(self):
        """Test metadata extraction for WAV files."""
        service = PlaceholderAudioService()

        mock_wav = MagicMock()
        mock_wav.info.bitrate = 705600

        mock_audio_segment = MagicMock()
        mock_audio_segment.channels = 1
        mock_audio_segment.frame_rate = 22050
        mock_audio_segment.sample_width = 2
        mock_audio_segment.__len__ = MagicMock(return_value=10000)  # 10 seconds in ms

        wav_data = b"RIFF\x00\x00\x00\x00WAVE"  # Fake WAV header

        with patch(
            "pydub.AudioSegment.from_file", return_value=mock_audio_segment
        ), patch("mutagen.mp3.MP3", side_effect=Exception("Not MP3")), patch(
            "adapter.audio.placeholder_audio_service.WAVE", return_value=mock_wav
        ):

            result = await service.get_audio_metadata(wav_data)

            assert result["duration_seconds"] == 10.0
            assert result["channels"] == 1
            assert result["sample_rate"] == 22050
            assert result["sample_width"] == 2
            assert result["size_bytes"] == len(wav_data)
            assert result["format"] == "wav"
            assert result["bitrate"] == 705600

    @pytest.mark.asyncio
    async def test_get_audio_metadata_unknown_format(self):
        """Test metadata extraction for unknown format."""
        service = PlaceholderAudioService()

        mock_audio_segment = MagicMock()
        mock_audio_segment.channels = 1
        mock_audio_segment.frame_rate = 44100
        mock_audio_segment.sample_width = 2
        mock_audio_segment.__len__ = MagicMock(return_value=5000)  # 5 seconds in ms

        unknown_data = b"UNKNOWN\x00\x00\x00\x00"  # Unknown header

        with patch(
            "pydub.AudioSegment.from_file", return_value=mock_audio_segment
        ), patch("mutagen.mp3.MP3", side_effect=Exception("Not MP3")), patch(
            "mutagen.wave.WAVE", side_effect=Exception("Not WAV")
        ), patch.object(
            service, "_detect_format_from_header", return_value="unknown"
        ):

            result = await service.get_audio_metadata(unknown_data)

            assert result["duration_seconds"] == 5.0
            assert result["format"] == "unknown"

    @pytest.mark.asyncio
    async def test_get_audio_metadata_empty_data(self):
        """Test metadata extraction with empty data raises ValueError."""
        service = PlaceholderAudioService()

        with pytest.raises(ValueError, match="Empty audio data provided"):
            await service.get_audio_metadata(b"")

    @pytest.mark.asyncio
    async def test_get_audio_metadata_pydub_failure(self):
        """Test metadata extraction when pydub fails."""
        service = PlaceholderAudioService()

        with patch(
            "pydub.AudioSegment.from_file", side_effect=Exception("Invalid audio")
        ):
            with pytest.raises(ValueError, match="Failed to extract audio metadata"):
                await service.get_audio_metadata(b"invalid")

    def test_generate_silence_wav(self):
        """Test WAV silence generation."""
        service = PlaceholderAudioService()

        result = service._generate_silence_wav(1.0)  # 1 second

        # Verify it's valid WAV data
        buffer = io.BytesIO(result)
        with wave.open(buffer, "rb") as wav_file:
            assert wav_file.getnchannels() == 1  # Mono
            assert wav_file.getsampwidth() == 2  # 16-bit
            assert wav_file.getframerate() == 22050
            assert wav_file.getnframes() == 22050  # 1 second * 22050 samples

    def test_detect_format_from_header_mp3_id3(self):
        """Test format detection for MP3 with ID3 header."""
        service = PlaceholderAudioService()

        mp3_data = b"ID3\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"  # 12 bytes
        assert service._detect_format_from_header(mp3_data) == "mp3"

    def test_detect_format_from_header_mp3_frame_sync(self):
        """Test format detection for MP3 with frame sync."""
        service = PlaceholderAudioService()

        mp3_data = b"\xff\xeb\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"  # MP3 frame sync
        assert service._detect_format_from_header(mp3_data) == "mp3"

    def test_detect_format_from_header_wav(self):
        """Test format detection for WAV."""
        service = PlaceholderAudioService()

        wav_data = b"RIFF\x00\x00\x00\x00WAVE\x00\x00\x00\x00"  # 12 bytes
        assert service._detect_format_from_header(wav_data) == "wav"

    def test_detect_format_from_header_ogg(self):
        """Test format detection for OGG."""
        service = PlaceholderAudioService()

        ogg_data = b"OggS\x00\x00\x00\x00\x00\x00\x00\x00"  # 12 bytes
        assert service._detect_format_from_header(ogg_data) == "ogg"

    def test_detect_format_from_header_flac(self):
        """Test format detection for FLAC."""
        service = PlaceholderAudioService()

        flac_data = b"fLaC\x00\x00\x00\x00\x00\x00\x00\x00"  # 12 bytes
        assert service._detect_format_from_header(flac_data) == "flac"

    def test_detect_format_from_header_aac(self):
        """Test format detection for AAC."""
        service = PlaceholderAudioService()

        aac_data = (
            b"\xff\xf1\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"  # ADTS sync + padding
        )
        assert service._detect_format_from_header(aac_data) == "aac"

    def test_detect_format_from_header_unknown(self):
        """Test format detection for unknown format."""
        service = PlaceholderAudioService()

        unknown_data = b"UNKNOWN\x00\x00\x00\x00"
        assert service._detect_format_from_header(unknown_data) == "unknown"

    def test_detect_format_from_header_short_data(self):
        """Test format detection with insufficient data."""
        service = PlaceholderAudioService()

        short_data = b"abc"
        assert service._detect_format_from_header(short_data) == "unknown"
