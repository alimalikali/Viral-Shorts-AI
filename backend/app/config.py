import os
from pathlib import Path

class Settings:
    APP_NAME: str = "Viral Shorts AI Backend"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))
    
    # Base paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    OUTPUT_DIR: Path = BASE_DIR / "outputs"
    TEMP_DIR: Path = BASE_DIR / "temp"
    PLUGINS_DIR: Path = BASE_DIR / "plugins"
    
    # AI Models config
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "base")  # tiny, base, small, medium, large-v3


    # Device configuration
    DEVICE: str = os.getenv("DEVICE", "cpu")  # cuda, cpu
    
    # Audio settings
    SAMPLE_RATE: int = 16000
    
    # Feature scoring multipliers
    WEIGHT_AUDIO_PEAK: float = 0.25
    WEIGHT_VISUAL_MOTION: float = 0.25
    WEIGHT_SCENE_CHANGE: float = 0.20
    WEIGHT_SEMANTIC_HOOK: float = 0.30

settings = Settings()

# Create directories immediately
for path in [settings.UPLOAD_DIR, settings.OUTPUT_DIR, settings.TEMP_DIR, settings.PLUGINS_DIR]:
    path.mkdir(parents=True, exist_ok=True)
