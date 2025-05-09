# config.py
import os

# API Keys
OPENAI_API_KEY = "YOUR_API_KEY"  # Replace with your actual OpenAI API key

# --- File and Directory Paths ---
# Root directory for data
DATA_DIR = "data"

# Input files and directories
VIDEO_DIR = os.path.join(DATA_DIR, "input_videos")
REFERENCE_AUDIO_DIR = os.path.join(DATA_DIR, "reference_audio")

# Output files and directories
OUTPUT_VIDEO_DIR = os.path.join(DATA_DIR, "output_videos")

# Temporary/Intermediate files
TEMP_DIR = os.path.join(DATA_DIR, "temp_files")
EXTRACTED_AUDIO_DIR = os.path.join(TEMP_DIR, "extracted_audio")
TTS_AUDIO_DIR = os.path.join(TEMP_DIR, "tts_audio_segments")
ADJUSTED_TTS_AUDIO_DIR = os.path.join(TEMP_DIR, "adjusted_tts_segments")
SYNCHRONIZED_AUDIO_DIR = os.path.join(TEMP_DIR, "synchronized_audio")

# Ensure temporary directories exist
TO_CREATE = [
    TEMP_DIR,
    EXTRACTED_AUDIO_DIR,
    TTS_AUDIO_DIR,
    ADJUSTED_TTS_AUDIO_DIR,
    SYNCHRONIZED_AUDIO_DIR
]
for path in TO_CREATE:
    os.makedirs(path, exist_ok=True)

# --- Default File Names ---
# These can be overridden or made dynamic in the main script
DEFAULT_VIDEO_FILENAME = "self-introduction.mp4" # Example, expecting it in VIDEO_DIR
DEFAULT_REFERENCE_AUDIO_FILENAME = "input_neeraj.m4a" # Example, expecting it in REFERENCE_AUDIO_DIR

# --- Transcription Settings ---
TRANSCRIPTION_MODEL = "base"
TRANSCRIPTION_LANGUAGE = "en"

# --- Translation Settings ---
TRANSLATION_MODEL = "gpt-3.5-turbo"
TARGET_LANGUAGE_NAME = "Hindi"
TARGET_LANGUAGE_CODE = "hi"

# --- TTS Settings ---
TTS_MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"
TTS_SPEED = 0.1 # Notebook had 0.1, adjust as needed

# --- Silence Detection --- 
SILENCE_THRESHOLD_DB = -40 # dBFS
SILENCE_CHUNK_SIZE_MS = 10 # milliseconds

# --- Audio Synchronization --- 
SYNCHRONIZATION_OFFSET_MS = 400 # milliseconds, for starting subsequent clips slightly earlier

# --- Video Output Settings ---
OUTPUT_VIDEO_CODEC = "libx264"
OUTPUT_AUDIO_CODEC = "aac"

print(f"Config loaded. Temp directories ensured at: {TEMP_DIR}") 