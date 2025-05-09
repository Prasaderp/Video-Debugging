# src/tts_generation.py
import os
import re
import torch
from TTS.api import TTS

import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import config

# TTS model instance, loaded on demand
tts_model = None

def load_tts_model():
    """Loads the TTS model specified in the config."""
    global tts_model
    if tts_model is None:
        print(f"Loading TTS model: {config.TTS_MODEL}")
        # Determine if GPU is available and should be used
        use_gpu = torch.cuda.is_available()
        print(f"TTS: CUDA available: {use_gpu}")
        try:
            tts_model = TTS(model_name=config.TTS_MODEL, gpu=use_gpu)
            print("TTS model loaded successfully.")
        except Exception as e:
            print(f"Error loading TTS model: {e}")
            print("If this is a 'config.json not found' error, the model might need to be downloaded or path is incorrect.")
            print("Attempting to load without GPU if GPU was tried.")
            if use_gpu:
                try:
                    tts_model = TTS(model_name=config.TTS_MODEL, gpu=False)
                    print("TTS model loaded successfully on CPU after GPU attempt failed.")
                except Exception as e_cpu:
                    print(f"Error loading TTS model on CPU as well: {e_cpu}")
                    tts_model = None # Ensure it's None if loading fails
            else:
                 tts_model = None # Ensure it's None if loading fails
    return tts_model

# Predefined dictionary for Hindi numbers (as in notebook)
# This could be expanded or made language-agnostic if needed.
HINDI_NUMBERS = {
    "0": "शून्य", "1": "एक", "2": "दो", "3": "तीन", "4": "चार", "5": "पांच", "6": "छह",
    "7": "सात", "8": "आठ", "9": "नौ", "10": "दस", "11": "ग्यारह", "12": "बारह",
    "13": "तेरह", "14": "चौदह", "15": "पंद्रह", "16": "सोलह", "17": "सत्रह",
    "18": "अठारह", "19": "उन्नीस", "20": "बीस", "21": "इक्कीस", "22": "बाईस",
    "23": "तेईस", "24": "चौबीस", "25": "पच्चीस", "26": "छब्बीस", "27": "सत्ताईस",
    "28": "अट्ठाईस", "29": "उनतीस", "30": "तीस", "40": "चालीस", "50": "पचास",
    "60": "साठ", "70": "सत्तर", "80": "अस्सी", "90": "नब्बे", "100": "सौ"
}

def _convert_numbers_to_hindi_words(match):
    """Helper to convert matched numbers to Hindi words using HINDI_NUMBERS dict."""
    num = match.group()
    return HINDI_NUMBERS.get(num, num) # Return original number if not in dict

def preprocess_tts_text(text, language_code=config.TARGET_LANGUAGE_CODE):
    """Preprocesses text for TTS: converts numbers to words (if Hindi) and removes certain punctuation."""
    if language_code == "hi": # Specific preprocessing for Hindi
        text = re.sub(r'\d+', _convert_numbers_to_hindi_words, text)
    # General preprocessing: remove periods that might cause TTS to pause unnaturally mid-sentence for some models
    # The Coqui TTS XTTS model handles punctuation well generally, so this might be aggressive.
    # The notebook had text = re.sub(r'\.\s*', ' ', text)
    # Let's make it more conservative: replace period only if not followed by a digit (e.g. 2.5)
    # and ensure it doesn't break sentences that should end.
    # Given XTTS handles sentences, this might be better handled by ensuring input text to TTS is single sentences.
    # For now, will keep it simple as per notebook for direct conversion:
    text = text.replace('.', '') # Removing all periods as per notebook. This is aggressive.
    text = text.replace('।', '') # Removing Hindi full stop (DANDA) as well, as TTS usually expects one sentence.
    text = text.strip()
    return text

def generate_tts_audio_segments(translated_sentences_with_timings, reference_speaker_wav_path, output_directory):
    """Generates TTS audio for each translated sentence and saves it as a separate file."""
    model = load_tts_model()
    if not model:
        print("TTS model not loaded. Cannot generate audio.")
        return []
    
    if not os.path.exists(reference_speaker_wav_path):
        print(f"Error: Reference speaker WAV file not found at {reference_speaker_wav_path}")
        return []

    os.makedirs(output_directory, exist_ok=True)
    generated_audio_files = []

    for i, sentence_info in enumerate(translated_sentences_with_timings):
        text_to_speak = sentence_info['text']
        # Preprocess text based on language (e.g., convert numbers for Hindi)
        processed_text = preprocess_tts_text(text_to_speak, config.TARGET_LANGUAGE_CODE)
        
        if not processed_text:
            print(f"Skipping TTS for sentence {i} as processed text is empty.")
            # Create a placeholder for empty audio or handle as error
            # For now, we skip and won't have a corresponding audio file
            continue
            
        output_filename = f"tts_segment_{i}.wav"
        output_path = os.path.join(output_directory, output_filename)

        try:
            print(f"Generating TTS for: \"{processed_text}\" (Lang: {config.TARGET_LANGUAGE_CODE})")
            model.tts_to_file(
                text=processed_text,
                file_path=output_path,
                speaker_wav=reference_speaker_wav_path,
                language=config.TARGET_LANGUAGE_CODE, 
                speed=config.TTS_SPEED
            )
            generated_audio_files.append(output_path)
            print(f"Generated TTS segment: {output_path}")
        except Exception as e:
            print(f"Error generating TTS for sentence {i} (\"{processed_text}\"): {e}")
            # Optionally, create a silent segment or skip
    
    return generated_audio_files


if __name__ == '__main__':
    print("Testing tts_generation.py...")

    # Ensure the reference audio directory exists as per config
    os.makedirs(config.REFERENCE_AUDIO_DIR, exist_ok=True)
    default_ref_audio = os.path.join(config.REFERENCE_AUDIO_DIR, config.DEFAULT_REFERENCE_AUDIO_FILENAME)

    if not os.path.exists(default_ref_audio):
        print(f"Reference audio {default_ref_audio} not found. Please place a reference audio file.")
        # Create a dummy silent m4a file if it doesn't exist, for basic testing flow
        # Note: TTS quality will be poor/non-existent with a silent reference.
        try:
            from pydub import AudioSegment
            silence = AudioSegment.silent(duration=1000) # 1 second
            silence.export(default_ref_audio, format="m4a")
            print(f"Created dummy silent reference audio: {default_ref_audio} for testing flow.")
        except Exception as e:
            print(f"Could not create dummy reference audio: {e}. TTS generation test may fail badly.")

    # Example translated sentences (these would come from the translation module)
    dummy_translated_sentences = [
        {'text': "नमस्ते, मेरा नाम जॉन है।", 'start': 0.5, 'end': 2.8},
        {'text': "मैं चौबीस साल का हूँ।", 'start': 3.0, 'end': 5.2},
        {'text': "यह एक परीक्षण वाक्य है।", 'start': 5.5, 'end': 8.0}
    ]
    
    print("\nTranslated Sentences (Input for TTS):")
    for s in dummy_translated_sentences:
        print(f"  [{s['start']:.2f}s - {s['end']:.2f}s] {s['text']}")

    # Test preprocessing
    print("\nTesting preprocessing:")
    test_text_hindi = "यह 24 सेब हैं। और यह 3.5 है."
    processed_hindi = preprocess_tts_text(test_text_hindi, "hi")
    print(f"Original Hindi: {test_text_hindi} -> Processed: {processed_hindi}")
    test_text_english = "This is 24 apples. And this is 3.5."
    processed_english = preprocess_tts_text(test_text_english, "en") # No number conversion for en
    print(f"Original English: {test_text_english} -> Processed: {processed_english}")

    if os.path.exists(default_ref_audio):
        tts_output_dir = os.path.join(config.TTS_AUDIO_DIR, "test_tts_output")
        generated_files = generate_tts_audio_segments(dummy_translated_sentences, default_ref_audio, tts_output_dir)
        
        if generated_files:
            print("\nGenerated TTS audio files:")
            for f_path in generated_files:
                print(f"  - {f_path}")
                if os.path.exists(f_path):
                    print(f"    (File exists, size: {os.path.getsize(f_path)} bytes)")
                else:
                    print("    (File NOT found!)")
        else:
            print("No TTS audio files were generated. Check logs for errors (e.g., model loading, reference audio).")
    else:
        print(f"Skipping TTS generation test as reference audio ({default_ref_audio}) is missing.")

    print("\ntts_generation.py test run finished.") 