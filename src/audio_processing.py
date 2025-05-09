# src/audio_processing.py
import os
import subprocess
from pydub import AudioSegment
import librosa
import pyrubberband
import soundfile as sf
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
import config

def extract_audio(video_path, audio_path):
    """Extracts audio from a video file using FFmpeg."""
    if os.path.exists(audio_path):
        print(f"Removing existing audio file: {audio_path}")
        os.remove(audio_path)
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", video_path, "-q:a", "0", "-map", "a", audio_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        print(f"Audio extracted successfully to {audio_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error extracting audio: {e}")
        print(f"FFmpeg stdout: {e.stdout}")
        print(f"FFmpeg stderr: {e.stderr}")
        raise

def get_audio_duration_ms(audio_path):
    """Gets the duration of an audio file in milliseconds."""
    audio = AudioSegment.from_wav(audio_path)
    return len(audio)

def detect_leading_silence(audio_path, silence_threshold_db=config.SILENCE_THRESHOLD_DB, chunk_size_ms=config.SILENCE_CHUNK_SIZE_MS):
    """Detects the duration of silence at the beginning of an audio file."""
    audio = AudioSegment.from_wav(audio_path)
    leading_silence_ms = 0
    for i in range(0, len(audio), chunk_size_ms):
        chunk = audio[i:i + chunk_size_ms]
        if chunk.dBFS > silence_threshold_db:
            break
        leading_silence_ms += chunk_size_ms
    return leading_silence_ms / 1000.0

def adjust_audio_clips_with_timings(audio_paths, timings, output_folder):
    """Adjusts each audio clip to match its target duration with speed adjustment and trimming using FFmpeg."""
    os.makedirs(output_folder, exist_ok=True)
    adjusted_paths = []
    for i, audio_path in enumerate(audio_paths):
        y, sr = librosa.load(audio_path, sr=None)
        current_duration_sec = librosa.get_duration(y=y, sr=sr)
        target_duration_sec = timings[i]['end'] - timings[i]['start']
        
        # Ensure target duration is positive
        if target_duration_sec <= 0:
            print(f"Warning: Target duration for clip {i} is zero or negative ({target_duration_sec}s). Skipping adjustment.")
            # Copy original file or create a very short silence if needed
            # For now, let's just use the original if target is invalid
            # sf.write(output_path, y, sr)
            # adjusted_paths.append(output_path)
            # continue
            target_duration_sec = 0.1 # Use a small positive duration
            print(f"Setting target duration to {target_duration_sec}s for clip {i}")


        speed_factor = current_duration_sec / target_duration_sec
        output_path = os.path.join(output_folder, f"adjusted_clip_{i}.wav")

        # Using pyrubberband for time-stretching (simpler than crafting complex ffmpeg filters for rubberband)
        # Rubberband recommends factors between 0.5 and 2.0 for best quality.
        # If factor is outside this, we might need multiple passes or accept quality loss.
        # For simplicity, we'll apply it directly. Pyrubberband handles complex factors.
        
        try:
            y_stretched = pyrubberband.pyrb.time_stretch(y, sr, speed_factor)

            # Trim or pad to the exact target duration
            target_samples = int(target_duration_sec * sr)
            current_samples = len(y_stretched)

            if current_samples > target_samples:
                y_final = y_stretched[:target_samples]
            elif current_samples < target_samples:
                padding = target_samples - current_samples
                y_final = librosa.util.pad_center(y_stretched, size=target_samples) # Pad with zeros
            else:
                y_final = y_stretched

            sf.write(output_path, y_final, sr)
            adjusted_paths.append(output_path)
        except Exception as e:
            print(f"Error adjusting clip {i} ({audio_path}) with pyrubberband: {e}")
            # Fallback: copy original if adjustment fails
            # sf.write(output_path, y, sr)
            # adjusted_paths.append(output_path)
            # Or handle more gracefully
            raise

    return adjusted_paths


def create_synchronized_audio(adjusted_audio_paths, timings, total_duration_ms, output_path, start_offset_ms=config.SYNCHRONIZATION_OFFSET_MS):
    """
    Creates synchronized audio by overlaying adjusted clips at adjusted start times.
    Applies an offset to all clips except the first one to start earlier.
    """
    # Ensure total_duration_ms is positive and an integer
    total_duration_ms = max(1, int(total_duration_ms)) # Ensure at least 1ms duration

    synchronized_audio = AudioSegment.silent(duration=total_duration_ms)
    for i, audio_path in enumerate(adjusted_audio_paths):
        try:
            clip = AudioSegment.from_wav(audio_path)
            # Apply offset only to clips after the first one (i > 0)
            offset = start_offset_ms if i > 0 else 0
            start_ms = max(0, int(timings[i]['start'] * 1000) - offset)  # Prevent negative start times
            
            # Ensure the clip is not overlaid beyond the bounds of synchronized_audio
            if start_ms + len(clip) > total_duration_ms:
                # Trim the clip if it extends beyond the total duration
                # This can happen if timings or offsets are aggressive
                clip = clip[:total_duration_ms - start_ms]
            
            if len(clip) > 0: # Only overlay if the clip has content
                 synchronized_audio = synchronized_audio.overlay(clip, position=start_ms)
            else:
                print(f"Warning: Clip {i} ({audio_path}) is empty or too short after adjustment/trimming. Skipping overlay.")

        except Exception as e:
            print(f"Error processing clip {i} ({audio_path}) for synchronization: {e}")
            # Optionally, skip this clip or handle error
            continue # Skip this clip if it cannot be processed
            
    synchronized_audio.export(output_path, format="wav")
    print(f"Synchronized audio saved at: {output_path}")
    return output_path

if __name__ == '__main__':
    # Example Usage (for testing this module directly)
    print("Testing audio_processing.py...")

    # Create dummy files and directories for testing if they don't exist
    os.makedirs(config.VIDEO_DIR, exist_ok=True)
    os.makedirs(config.EXTRACTED_AUDIO_DIR, exist_ok=True)
    os.makedirs(config.TEMP_DIR, exist_ok=True)
    os.makedirs(config.ADJUSTED_TTS_AUDIO_DIR, exist_ok=True)
    os.makedirs(config.SYNCHRONIZED_AUDIO_DIR, exist_ok=True)

    # Create a dummy video file (e.g., a silent mp4 or a copy of a real one for testing)
    # For this example, we'll assume a video 'test_video.mp4' exists in config.VIDEO_DIR
    test_video_name = "test_video.mp4"
    test_video_path = os.path.join(config.VIDEO_DIR, test_video_name)
    
    # Create a small, silent MP4 file if it doesn't exist for testing extract_audio
    if not os.path.exists(test_video_path):
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100", 
                 "-f", "lavfi", "-i", "color=c=blue:s=1280x720:d=1", 
                 "-t", "1", "-c:v", "libx264", "-c:a", "aac", test_video_path],
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            print(f"Created dummy video for testing: {test_video_path}")
        except Exception as e:
            print(f"Could not create dummy video: {e}. extract_audio test might fail if video doesn't exist.")


    extracted_audio_filename = f"{os.path.splitext(test_video_name)[0]}_extracted.wav"
    extracted_audio_path = os.path.join(config.EXTRACTED_AUDIO_DIR, extracted_audio_filename)

    if os.path.exists(test_video_path):
        extract_audio(test_video_path, extracted_audio_path)
        if os.path.exists(extracted_audio_path):
            duration = get_audio_duration_ms(extracted_audio_path)
            print(f"Extracted audio duration: {duration} ms")
            leading_silence = detect_leading_silence(extracted_audio_path)
            print(f"Leading silence: {leading_silence} s")

            # Dummy data for adjust_audio_clips_with_timings and create_synchronized_audio
            # Create some dummy WAV files to act as TTS segments
            dummy_tts_segments_dir = os.path.join(config.TEMP_DIR, "dummy_tts_segments")
            os.makedirs(dummy_tts_segments_dir, exist_ok=True)
            dummy_audio_paths = []
            for i in range(2):
                dummy_file_path = os.path.join(dummy_tts_segments_dir, f"dummy_segment_{i}.wav")
                # Create a 1-second silent wav file
                try:
                    segment = AudioSegment.silent(duration=1000) # 1 second
                    segment.export(dummy_file_path, format="wav")
                    dummy_audio_paths.append(dummy_file_path)
                except Exception as e:
                    print(f"Failed to create dummy segment {i}: {e}")
            
            if dummy_audio_paths: # Proceed only if dummy segments were created
                dummy_timings = [
                    {'start': 0.0, 'end': 0.8}, 
                    {'start': 0.9, 'end': 1.5}
                ]
                
                adjusted_clips_path = os.path.join(config.ADJUSTED_TTS_AUDIO_DIR, "test_adjusted")
                adjusted_paths = adjust_audio_clips_with_timings(dummy_audio_paths, dummy_timings, adjusted_clips_path)
                print(f"Adjusted dummy clips: {adjusted_paths}")

                if adjusted_paths and os.path.exists(extracted_audio_path):
                    total_original_duration_ms = get_audio_duration_ms(extracted_audio_path)
                    sync_output_path = os.path.join(config.SYNCHRONIZED_AUDIO_DIR, "test_synchronized_output.wav")
                    create_synchronized_audio(adjusted_paths, dummy_timings, total_original_duration_ms, sync_output_path)
                else:
                    print("Skipping synchronization test due to missing adjusted paths or extracted audio.")
            else:
                print("Skipping adjustment and synchronization tests as dummy TTS segments could not be created.")
        else:
            print(f"Extracted audio not found at {extracted_audio_path}. Skipping further tests for it.")
    else:
        print(f"Test video not found at {test_video_path}. Skipping extract_audio and subsequent tests.")

    print("Audio_processing.py test run finished.") 