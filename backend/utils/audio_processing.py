import numpy as np
import librosa
import io
from scipy import signal
import soundfile as sf


def preprocess_audio(audio_bytes: bytes, target_sr: int = 16000) -> np.ndarray:
    """
    Preprocess audio data for better transcription quality
    """
    # Load audio from bytes
    audio_buffer = io.BytesIO(audio_bytes)
    audio_data, sr = librosa.load(audio_buffer, sr=None)
    
    # Resample to target sample rate if needed
    if sr != target_sr:
        audio_data = librosa.resample(audio_data, orig_sr=sr, target_sr=target_sr)
        sr = target_sr
    
    # Apply noise reduction (simple spectral gating)
    audio_data = reduce_noise_simple(audio_data)
    
    # Normalize audio
    audio_data = normalize_audio(audio_data)
    
    return audio_data


def reduce_noise_simple(audio_data: np.ndarray, n_fft: int = 2048, hop_length: int = 512) -> np.ndarray:
    """
    Simple noise reduction using spectral gating
    """
    # Compute STFT
    stft = librosa.stft(audio_data, n_fft=n_fft, hop_length=hop_length)
    magnitude = np.abs(stft)
    phase = np.angle(stft)
    
    # Estimate noise floor (using median of lowest 10% of magnitudes)
    noise_floor = np.percentile(magnitude, 10, axis=1, keepdims=True)
    
    # Create mask to suppress noise
    mask = magnitude > noise_floor * 1.5  # Only keep components significantly louder than noise
    
    # Apply mask
    magnitude_denoised = magnitude * mask
    
    # Reconstruct audio
    stft_denoised = magnitude_denoised * np.exp(1j * phase)
    audio_denoised = librosa.istft(stft_denoised, hop_length=hop_length)
    
    return audio_denoised.astype(audio_data.dtype)


def normalize_audio(audio_data: np.ndarray) -> np.ndarray:
    """
    Normalize audio to standard loudness level
    """
    # Peak normalization
    max_amplitude = np.max(np.abs(audio_data))
    if max_amplitude > 0:
        audio_data = audio_data / max_amplitude
        # Scale to reasonable range (-0.9 to 0.9 to avoid clipping)
        audio_data = audio_data * 0.9
    
    return audio_data


def detect_silence(audio_data: np.ndarray, threshold: float = 0.01, frame_length: int = 2048) -> np.ndarray:
    """
    Detect silence frames in audio
    """
    # Calculate energy for each frame
    frames = librosa.util.frame(audio_data, frame_length=frame_length, hop_length=frame_length//2)
    energy = np.sum(frames**2, axis=0)
    
    # Normalize energy
    energy = energy / np.max(energy) if np.max(energy) > 0 else energy
    
    # Detect silence (below threshold)
    silence_mask = energy < threshold
    
    return silence_mask


def enhance_speech_features(audio_data: np.ndarray, sr: int = 16000) -> dict:
    """
    Extract speech enhancement features for analysis
    """
    features = {}
    
    # Zero crossing rate (indicates noisiness)
    zcr = librosa.feature.zero_crossing_rate(audio_data)[0]
    features['zero_crossing_rate_mean'] = np.mean(zcr)
    
    # Spectral centroid (indicates brightness)
    spectral_centroids = librosa.feature.spectral_centroid(y=audio_data, sr=sr)[0]
    features['spectral_centroid_mean'] = np.mean(spectral_centroids)
    
    # MFCCs (Mel-frequency cepstral coefficients)
    mfccs = librosa.feature.mfcc(y=audio_data, sr=sr, n_mels=13)
    features['mfcc_means'] = np.mean(mfccs, axis=1).tolist()
    
    # RMS energy
    rms = librosa.feature.rms(y=audio_data)[0]
    features['rms_energy_mean'] = np.mean(rms)
    features['rms_energy_std'] = np.std(rms)
    
    # Pitch features (if possible)
    try:
        pitches, magnitudes = librosa.piptrack(y=audio_data, sr=sr)
        pitch_values = pitches[magnitudes > np.median(magnitudes)]
        pitch_values = pitch_values[pitch_values > 0]  # Filter out zero values
        
        if len(pitch_values) > 0:
            features['pitch_mean'] = np.mean(pitch_values)
            features['pitch_std'] = np.std(pitch_values)
        else:
            features['pitch_mean'] = 0
            features['pitch_std'] = 0
    except:
        features['pitch_mean'] = 0
        features['pitch_std'] = 0
    
    return features