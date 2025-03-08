# Video Translation Tool: English to Hindi  

A robust Python-based utility for translating English video content into Hindi, featuring audio extraction, transcription, translation, text-to-speech synthesis, and seamless audio-video synchronization.  

## Overview  

This project automates the process of converting English-language videos into Hindi by leveraging state-of-the-art libraries and APIs. It preserves timing accuracy and maintains high-quality audio output, making it suitable for professional dubbing and localization tasks.  

## Key Features  

- **Audio Extraction**: Extracts audio from video using FFmpeg.  
- **Transcription**: Generates timestamped English transcripts with Whisper.  
- **Translation**: Converts English text to Hindi using OpenAI GPT-3.5, preserving sentence structure and punctuation.  
- **TTS Synthesis**: Produces natural-sounding Hindi audio with the TTS library.  
- **Synchronization**: Aligns translated audio with original video timings.  
- **Video Integration**: Replaces original audio with translated Hindi audio using MoviePy.  

## Prerequisites  

- Python 3.8+  
- FFmpeg installed on your system  
- GPU support (optional, for faster processing)  

## Installation  

Install dependencies in a compatible environment (e.g., Google Colab):  

```bash
sudo apt-get install -y rubberband-cli  
pip install pyrubberband librosa soundfile pydub openai-whisper openai moviepy  
pip install TTS  
```

**Note**: Replace `YOUR_API_KEY` in the script with your OpenAI API key.  

## Usage  

1. **Prepare Input**: Place your English video file (e.g., `self-introduction.mp4`) in the working directory.  
2. **Configure Paths**: Update `video_path` and `audio_path` variables in the script.  
3. **Execute**: Run the script to process the video and generate a Hindi-dubbed output.  
4. **Output**: Retrieve the translated video (e.g., `self-introduction_final.mp4`).  

## Sample Configuration  

```python
video_path = "/content/self-introduction.mp4"  
audio_path = "/content/self-introduction_audio.wav"  
```

## Workflow  

1. Extracts audio from the video.  
2. Transcribes audio into English with timing data.  
3. Translates into Hindi while maintaining structure.  
4. Generates Hindi audio via TTS.  
5. Adjusts audio clips to match original durations.  
6. Synchronizes and integrates translated audio into the video.  

## Output Example  

- **Input**: English self-introduction video (1 minute).  
- **Output**: Hindi-dubbed video with synchronized audio.  

## Limitations  

- Requires a stable internet connection for API calls.  
- Performance may vary based on hardware (GPU recommended).  
- Designed for English-to-Hindi; additional languages require customization.  

## Contributing  

Contributions are welcome. To contribute:  

1. Fork the repository.  
2. Submit pull requests with improvements.  
3. Report issues via the GitHub Issues tab.  
