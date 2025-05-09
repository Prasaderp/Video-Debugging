# src/transcription.py
import os
import whisper
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
import config
from src.audio_processing import detect_leading_silence #, get_audio_duration_ms

def load_transcription_model(model_name=config.TRANSCRIPTION_MODEL):
    """Loads the Whisper transcription model."""
    print(f"Loading Whisper model: {model_name}")
    model = whisper.load_model(model_name)
    print("Whisper model loaded.")
    return model

def transcribe_audio(model, audio_path, language=config.TRANSCRIPTION_LANGUAGE):
    """Transcribes audio using the loaded Whisper model."""
    print(f"Transcribing audio: {audio_path} for language: {language}")
    transcript = model.transcribe(
        audio=audio_path,
        language=language,
        word_timestamps=True
    )
    print("Transcription complete.")
    # print(f"Raw transcript text: {transcript['text']}")
    return transcript

def process_transcription_into_sentences(transcript, leading_silence_sec):
    """Processes the Whisper transcript into sentences with adjusted start/end timings."""
    sentences = []
    current_sentence_words = []
    sentence_start_time = None
    last_word_end_time = 0.0 # Initialize to 0.0

    # Ensure segments are present and not empty
    if not transcript or 'segments' not in transcript or not transcript['segments']:
        print("Warning: Transcription segments are empty or missing.")
        return []

    for segment_idx, segment in enumerate(transcript['segments']):
        # Ensure words are present in the segment
        if 'words' not in segment or not segment['words']:
            # print(f"Warning: Segment {segment_idx} has no words. Skipping.")
            continue

        for word_info in segment['words']:
            # Ensure word_info is a dictionary and has 'start', 'end', 'word'
            if not isinstance(word_info, dict) or not all(k in word_info for k in ('start', 'end', 'word')):
                print(f"Warning: Invalid word_info format: {word_info}. Skipping.")
                continue
            
            # Adjust start and end times with leading silence
            # The whisper timestamps are relative to the start of the audio fed to it.
            # If detect_leading_silence was applied to the *same* audio, this adjustment is correct.
            adjusted_start = word_info['start'] + leading_silence_sec
            adjusted_end = word_info['end'] + leading_silence_sec
            word_text = word_info['word']

            if not current_sentence_words:
                sentence_start_time = adjusted_start
            
            current_sentence_words.append(word_text)
            last_word_end_time = adjusted_end # Keep track of the last word's end time

            # Check if the word ends a sentence
            if word_text.strip().endswith(('.', '?', '!')):
                sentence_text = ''.join(current_sentence_words) # Use join without space for better punctuation handling, then strip
                sentences.append({
                    'text': sentence_text.strip(),
                    'start': sentence_start_time,
                    'end': adjusted_end # End of the word that terminates the sentence
                })
                current_sentence_words = []
                sentence_start_time = None
    
    # Add any remaining words as the last sentence
    if current_sentence_words:
        sentence_text = ''.join(current_sentence_words)
        # If sentence_start_time is None here, it means the transcript was very short 
        # and didn't hit punctuation. Use the start of the first word as sentence_start_time.
        if sentence_start_time is None and transcript['segments'] and transcript['segments'][0]['words']:
             first_word_start = transcript['segments'][0]['words'][0]['start'] + leading_silence_sec
             sentence_start_time = first_word_start
        
        # Ensure last_word_end_time is valid for the final sentence
        if sentence_start_time is not None : # only append if we have a valid start time
            sentences.append({
                'text': sentence_text.strip(),
                'start': sentence_start_time,
                'end': last_word_end_time # Use the end time of the very last word processed
            })

    print(f"Processed {len(sentences)} sentences from transcript.")
    return sentences

if __name__ == '__main__':
    print("Testing transcription.py...")
    
    # Dummy audio path - replace with a real one for actual testing
    # This test needs an actual audio file to run whisper.
    # Using the one from audio_processing test if it exists
    dummy_extracted_audio_dir = os.path.join(config.EXTRACTED_AUDIO_DIR)
    dummy_audio_filename = "test_video_extracted.wav"
    test_audio_path = os.path.join(dummy_extracted_audio_dir, dummy_audio_filename)

    if not os.path.exists(test_audio_path):
        print(f"Test audio file not found: {test_audio_path}")
        print("Please run audio_processing.py tests first to generate it, or provide a valid WAV file.")
    else:
        print(f"Using test audio: {test_audio_path}")
        # 1. Detect leading silence (from audio_processing module)
        # Make sure audio_processing.py is in the python path or same directory for this import
        silence_sec = detect_leading_silence(test_audio_path)
        print(f"Detected leading silence: {silence_sec:.2f}s")

        # 2. Load transcription model
        model = load_transcription_model()

        # 3. Transcribe audio
        transcript_result = transcribe_audio(model, test_audio_path)
        # print("Full transcript object:", transcript_result)

        # 4. Process into sentences
        if transcript_result:
            processed_sentences = process_transcription_into_sentences(transcript_result, silence_sec)
            print("\nProcessed Sentences with Timings:")
            for i, sentence_info in enumerate(processed_sentences):
                print(f"  {i+1}. [{sentence_info['start']:.2f}s - {sentence_info['end']:.2f}s] {sentence_info['text']}")
        else:
            print("Transcription result was empty, cannot process sentences.")

    print("transcription.py test run finished.") 