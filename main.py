# main.py
import os
import time
import shutil # For cleaning up temp directories

# Ensure src modules can be imported if main.py is in the root
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

import config
from src.audio_processing import (
    extract_audio,
    get_audio_duration_ms,
    detect_leading_silence,
    adjust_audio_clips_with_timings,
    create_synchronized_audio
)
from src.transcription import (
    load_transcription_model,
    transcribe_audio,
    process_transcription_into_sentences
)
from src.translation import (
    translate_sentences_to_target_lang,
    pair_translated_sentences_with_timings,
    initialize_openai_client # Ensure client is initialized if not already
)
from src.tts_generation import (
    generate_tts_audio_segments,
    load_tts_model # To preload if desired
)
from src.video_processing import replace_audio_in_video

def main_pipeline(video_filename, reference_audio_filename, output_video_filename_base):
    """Runs the full video translation and dubbing pipeline."""
    start_time = time.time()

    # --- 0. Setup Paths --- 
    input_video_path = os.path.join(config.VIDEO_DIR, video_filename)
    reference_speaker_path = os.path.join(config.REFERENCE_AUDIO_DIR, reference_audio_filename)
    
    # Create unique names for intermediate and final files based on input video name
    base_name = os.path.splitext(video_filename)[0]
    extracted_audio_name = f"{base_name}_extracted.wav"
    extracted_audio_path = os.path.join(config.EXTRACTED_AUDIO_DIR, extracted_audio_name)

    tts_segments_output_dir = os.path.join(config.TTS_AUDIO_DIR, base_name)
    adjusted_tts_segments_output_dir = os.path.join(config.ADJUSTED_TTS_AUDIO_DIR, base_name)
    synchronized_audio_name = f"{base_name}_synchronized_dubbed.wav"
    synchronized_audio_path = os.path.join(config.SYNCHRONIZED_AUDIO_DIR, synchronized_audio_name)
    
    final_output_video_name = f"{output_video_filename_base}_{config.TARGET_LANGUAGE_CODE}.mp4"
    final_output_video_path = os.path.join(config.OUTPUT_VIDEO_DIR, final_output_video_name)

    print(f"--- Starting Video Dubbing Pipeline for: {video_filename} ---")
    print(f"Output will be: {final_output_video_path}")

    # --- Check Inputs ---
    if not os.path.exists(input_video_path):
        print(f"Error: Input video not found: {input_video_path}")
        return
    if not os.path.exists(reference_speaker_path):
        print(f"Error: Reference speaker audio not found: {reference_speaker_path}")
        return
    
    # Initialize OpenAI client (it has a check so it only initializes once)
    initialize_openai_client()
    if not config.client: # from translation module
        print("OpenAI client failed to initialize (check API key). Aborting.")
        return

    # Pre-load TTS model (optional, can reduce first-time lag in generate_tts_audio_segments)
    if not load_tts_model():
        print("TTS model failed to load. Aborting.")
        return
    transcription_model_instance = load_transcription_model()
    if not transcription_model_instance:
        print("Transcription model failed to load. Aborting.")
        return

    try:
        # --- 1. Extract Audio from Video ---
        print("\nStep 1: Extracting Audio...")
        extract_audio(input_video_path, extracted_audio_path)
        original_audio_duration_ms = get_audio_duration_ms(extracted_audio_path)
        print(f"Original audio duration: {original_audio_duration_ms / 1000:.2f}s")

        # --- 2. Detect Leading Silence --- 
        print("\nStep 2: Detecting Leading Silence...")
        leading_silence_sec = detect_leading_silence(extracted_audio_path)
        print(f"Leading silence: {leading_silence_sec:.2f}s")

        # --- 3. Transcribe Audio ---
        print("\nStep 3: Transcribing Audio...")
        transcript_data = transcribe_audio(transcription_model_instance, extracted_audio_path)
        english_sentences = process_transcription_into_sentences(transcript_data, leading_silence_sec)
        if not english_sentences:
            print("Error: No sentences extracted from transcription. Aborting.")
            return
        print(f"Transcribed {len(english_sentences)} English sentences.")
        # for i, s in enumerate(english_sentences): print(f"  {i+1}. [{s['start']:.2f}-{s['end']:.2f}] {s['text']}")

        # --- 4. Translate Sentences ---
        print(f"\nStep 4: Translating to {config.TARGET_LANGUAGE_NAME}...")
        translated_sentence_strings = translate_sentences_to_target_lang(english_sentences)
        if not translated_sentence_strings:
            print("Error: Translation failed. Aborting.")
            return
        target_lang_sentences_with_timings = pair_translated_sentences_with_timings(translated_sentence_strings, english_sentences)
        if not target_lang_sentences_with_timings:
            print("Error: Pairing translated sentences with timings failed. Aborting.")
            return
        print(f"Translated and paired {len(target_lang_sentences_with_timings)} sentences.")
        # for i, s in enumerate(target_lang_sentences_with_timings): print(f"  {i+1}. [{s['start']:.2f}-{s['end']:.2f}] {s['text']}")

        # --- 5. Generate TTS Audio Segments ---
        print("\nStep 5: Generating TTS Audio Segments...")
        tts_audio_segment_paths = generate_tts_audio_segments(target_lang_sentences_with_timings, reference_speaker_path, tts_segments_output_dir)
        if not tts_audio_segment_paths or len(tts_audio_segment_paths) != len(target_lang_sentences_with_timings):
            print("Error: TTS generation failed or mismatch in segment count. Aborting.")
            return
        print(f"Generated {len(tts_audio_segment_paths)} TTS audio segments.")

        # --- 6. Adjust TTS Audio Timings ---
        print("\nStep 6: Adjusting TTS Audio Timings...")
        adjusted_audio_segment_paths = adjust_audio_clips_with_timings(tts_audio_segment_paths, target_lang_sentences_with_timings, adjusted_tts_segments_output_dir)
        if not adjusted_audio_segment_paths:
            print("Error: Adjusting audio clips failed. Aborting.")
            return
        print(f"Adjusted {len(adjusted_audio_segment_paths)} audio segments.")

        # --- 7. Create Synchronized Dubbed Audio Track ---
        print("\nStep 7: Creating Synchronized Dubbed Audio Track...")
        create_synchronized_audio(adjusted_audio_segment_paths, target_lang_sentences_with_timings, original_audio_duration_ms, synchronized_audio_path)
        print(f"Synchronized audio track saved to: {synchronized_audio_path}")

        # --- 8. Replace Audio in Original Video ---
        print("\nStep 8: Replacing Audio in Video...")
        replace_audio_in_video(input_video_path, synchronized_audio_path, final_output_video_path)
        
        total_time = time.time() - start_time
        print(f"\n--- Pipeline Completed for {video_filename} in {total_time:.2f} seconds ---")
        print(f"Final dubbed video saved to: {final_output_video_path}")

    except Exception as e:
        print(f"An error occurred during the pipeline: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # --- Optional: Clean up temporary segment directories ---
        # Consider making this configurable
        # print("\nCleaning up temporary segment directories...")
        # if os.path.exists(tts_segments_output_dir):
        #     shutil.rmtree(tts_segments_output_dir)
        #     print(f"Removed: {tts_segments_output_dir}")
        # if os.path.exists(adjusted_tts_segments_output_dir):
        #     shutil.rmtree(adjusted_tts_segments_output_dir)
        #     print(f"Removed: {adjusted_tts_segments_output_dir}")
        # Extracted audio and final synchronized audio are kept in temp for now.
        pass

if __name__ == "__main__":
    # Ensure API key is set in config.py before running.
    if config.OPENAI_API_KEY == "YOUR_API_KEY" or not config.OPENAI_API_KEY:
        print("ERROR: OpenAI API key is not set in config.py. Please set it to run the main pipeline.")
        print("You can find config.py in the root of the project.")
        exit(1)

    # Example usage:
    # Make sure these files exist in the configured data directories (config.VIDEO_DIR, config.REFERENCE_AUDIO_DIR)
    # You might need to copy your 'self-introduction.mp4' and 'input_neeraj.m4a' to these locations.
    
    # Example: Copying test files if they are not in the designated folders
    # This is just for demonstration if you run this directly without placing files.
    example_video = config.DEFAULT_VIDEO_FILENAME
    example_ref_audio = config.DEFAULT_REFERENCE_AUDIO_FILENAME

    # Check if example files exist, provide guidance if not.
    if not os.path.exists(os.path.join(config.VIDEO_DIR, example_video)):
        print(f"Warning: Default video '{example_video}' not found in '{config.VIDEO_DIR}'. Pipeline might fail.")
        print("Please place your input video there or update config.DEFAULT_VIDEO_FILENAME and the call below.")
    
    if not os.path.exists(os.path.join(config.REFERENCE_AUDIO_DIR, example_ref_audio)):
        print(f"Warning: Default reference audio '{example_ref_audio}' not found in '{config.REFERENCE_AUDIO_DIR}'. Pipeline might fail.")
        print("Please place your reference audio there or update config.DEFAULT_REFERENCE_AUDIO_FILENAME and the call below.")

    # Define the base for the output filename (language code will be appended)
    output_filename_base = os.path.splitext(example_video)[0] + "_dubbed"

    main_pipeline(example_video, example_ref_audio, output_filename_base) 