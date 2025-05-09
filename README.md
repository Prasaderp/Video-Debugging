# Video Language Translator & Dubber

This project provides a pipeline to translate the spoken language in a video to a target language (e.g., English to Hindi) and then dub the video with a new audio track generated using Text-to-Speech (TTS) in the target language, attempting to synchronize it with the original speech timings.

## Features

- Extracts audio from an input video file.
- Transcribes the original audio to text using OpenAI Whisper.
- Adjusts transcription timings based on detected leading silence.
- Translates the transcribed text to a specified target language using OpenAI GPT models.
- Generates speech for the translated text using Coqui TTS, using a reference speaker's voice.
- Adjusts the speed and duration of the generated TTS audio segments to match the original sentence timings.
- Combines the adjusted TTS segments into a single synchronized audio track.
- Replaces the original audio in the video with the new dubbed audio track.

## Project Structure

```
. 
├── main.py                  # Main script to run the full pipeline
├── config.py                # Configuration for API keys, paths, models, etc.
├── requirements.txt         # Python dependencies
├── README.md                # This file
├── src/                     # Source code modules
│   ├── __init__.py          # Makes src a package (can be empty)
│   ├── audio_processing.py  # Audio extraction, silence detection, speed adjustment, combining
│   ├── transcription.py     # Whisper transcription and sentence segmentation
│   ├── translation.py       # OpenAI translation and timing pairing
│   ├── tts_generation.py    # Coqui TTS audio generation
│   └── video_processing.py  # Replacing audio in video
└── data/                    # Data directory (not committed to git by default)
    ├── input_videos/        # Place your input video files here (e.g., self-introduction.mp4)
    ├── reference_audio/     # Place your reference speaker audio WAV/M4A here (e.g., input_neeraj.m4a)
    ├── output_videos/       # Dubbed videos will be saved here
    └── temp_files/          # Intermediate files (extracted audio, TTS segments, etc.)
        ├── extracted_audio/
        ├── tts_audio_segments/
        ├── adjusted_tts_segments/
        └── synchronized_audio/
```

## Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Prasaderp/Video-Debugging.git
    cd Video-Debugging
    ```

2.  **Create a Python virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Windows
    venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install FFmpeg:**
    FFmpeg is required for audio extraction and some audio processing. Ensure it's installed and accessible in your system's PATH.
    -   Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH.
    -   macOS (using Homebrew): `brew install ffmpeg`
    -   Linux (using apt): `sudo apt update && sudo apt install ffmpeg`

4.  **Install `rubberband-cli` (for `pyrubberband` time-stretching):**
    The notebook uses `apt-get install -y rubberband-cli`. 
    -   Linux (using apt): `sudo apt install rubberband-cli`
    -   macOS (using Homebrew): `brew install rubberband`
    -   Windows: This might be trickier. You may need to find a precompiled binary or build from source. `pyrubberband` might work without it if it can find the library, but `rubberband-cli` provides the command-line tool it often wraps.

5.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    If you encounter issues with PyTorch/CUDA, you might need to install a specific version from [pytorch.org](https://pytorch.org/) that matches your CUDA toolkit version if you intend to use GPU for TTS or Whisper.

6.  **Configure API Keys and Paths:**
    -   Open `config.py`.
    -   Set your `OPENAI_API_KEY`.
    -   Review other paths and model settings if needed. The default paths assume you place your input video in `data/input_videos/` and reference speaker audio in `data/reference_audio/`.

7.  **Place Input Files:**
    -   Put your input video (e.g., `self-introduction.mp4`) into the `data/input_videos/` directory.
    -   Put your reference speaker audio file (e.g., `input_neeraj.m4a` or a WAV file) into the `data/reference_audio/` directory.
    -   Update `DEFAULT_VIDEO_FILENAME` and `DEFAULT_REFERENCE_AUDIO_FILENAME` in `config.py` or pass them as arguments if you modify `main.py` to accept them.

## Running the Pipeline

Once setup is complete, you can run the main pipeline script:

```bash
python main.py
```

This will process the video specified by `DEFAULT_VIDEO_FILENAME` in `config.py` (or as modified in `main.py`), using the reference speaker audio specified by `DEFAULT_REFERENCE_AUDIO_FILENAME`.

The final dubbed video will be saved in the `data/output_videos/` directory.

## Notes & Potential Issues

*   **Model Downloads:** The first time you run the script, Whisper and Coqui TTS models will be downloaded. This might take some time.
*   **API Costs:** Using the OpenAI API for transcription (if Whisper API is chosen over local) and translation will incur costs.
*   **TTS Quality:** The quality of the dubbed audio depends heavily on the TTS model and the quality/similarity of the reference speaker audio.
*   **Synchronization:** The synchronization is based on sentence timings and speed adjustments. Perfect lip-sync is not guaranteed and is a very complex problem.
*   **Error Handling:** The scripts include basic error handling, but complex failures in external libraries (FFmpeg, model loading) might require specific troubleshooting.
*   **Resource Usage:** Transcription and TTS can be resource-intensive, especially on CPU. A GPU is recommended for better performance with Whisper and Coqui TTS.
*   **`rubberband-cli` on Windows:** If `pyrubberband` cannot find the `rubberband` library or `rubberband-cli`, the `adjust_audio_clips_with_timings` function in `audio_processing.py` might fail. You might need to adapt it to use a different time-stretching method or ensure `rubberband` is correctly installed and accessible.

## Customization

-   **Target Language:** Change `TARGET_LANGUAGE_NAME` and `TARGET_LANGUAGE_CODE` in `config.py`.
-   **Models:** Update model names for Whisper, OpenAI, and TTS in `config.py`.
-   **Paths:** Modify directory paths in `config.py`.
-   **Parameters:** Adjust TTS speed, silence detection thresholds, etc., in `config.py`.
