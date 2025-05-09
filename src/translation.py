# src/translation.py
import os
import re
from openai import OpenAI
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
import config

client = None

def initialize_openai_client():
    global client
    if config.OPENAI_API_KEY == "YOUR_API_KEY" or not config.OPENAI_API_KEY:
        print("Warning: OPENAI_API_KEY is not set in config.py. Translation will not work.")
        client = None
        return
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    print("OpenAI client initialized.")

# Call initialization when the module is loaded.
initialize_openai_client()

def translate_sentences_to_target_lang(english_sentences_with_timings):
    """Translates a list of English sentences to the target language using OpenAI GPT.
    Args:
        english_sentences_with_timings (list): List of dicts, each with 'text', 'start', 'end'.
    Returns:
        list: List of translated sentence strings, or None if translation fails.
    """
    if not client:
        print("OpenAI client not initialized. Cannot translate.")
        return None
    if not english_sentences_with_timings:
        print("No sentences provided for translation.")
        return []

    # Constructing the prompt for batch translation for better context
    # and to respect sentence boundaries.
    prompt_parts = [
        f"Translate the following English text to {config.TARGET_LANGUAGE_NAME}. "
        f"Each sentence is numbered. Provide the translation for each numbered sentence. "
        f"Maintain the original sentence count and structure as much as possible. "
        f"For example, if there are 3 input sentences, provide 3 translated sentences."
        f"Do not add any extra information, comments, or change the order."
        f"Preserve original punctuation if it makes sense in {config.TARGET_LANGUAGE_NAME}."
        "Input English sentences:"
    ]
    for i, sent_info in enumerate(english_sentences_with_timings):
        prompt_parts.append(f"{i+1}. {sent_info['text']}")
    
    full_prompt = "\n".join(prompt_parts)
    # print(f"\nTranslation Prompt:\n{full_prompt}\n")

    try:
        response = client.chat.completions.create(
            model=config.TRANSLATION_MODEL,
            messages=[
                {"role": "system", "content": f"You are a professional translator specializing in English to {config.TARGET_LANGUAGE_NAME} translation for audiovisual content. Respond only with the translated sentences, each on a new line, numbered like the input."}, 
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.2,
            max_tokens=2000 # Adjust as needed based on text length
        )
        raw_translated_text = response.choices[0].message.content.strip()
        # print(f"\nRaw translation output:\n{raw_translated_text}\n")

        # Extract and clean translations from the numbered output
        # This regex looks for lines starting with a number and a dot, then captures the text.
        parsed_translations = re.findall(r"^\s*\d+\.\s*(.*?)(?=\n\s*\d+\.|$)", raw_translated_text, re.MULTILINE | re.DOTALL)
        cleaned_translations = [text.strip() for text in parsed_translations]

        if len(cleaned_translations) != len(english_sentences_with_timings):
            print(f"Warning: Mismatch in translated sentence count. Expected {len(english_sentences_with_timings)}, got {len(cleaned_translations)}.")
            print(f"Raw output was: {raw_translated_text}")
            # Attempt to fallback by splitting the raw text by newlines if counts don't match
            # This is a heuristic and might not always be correct.
            cleaned_translations = [line.strip() for line in raw_translated_text.split('\n') if line.strip()]
            # Remove any numbering if present in this fallback
            cleaned_translations = [re.sub(r"^\s*\d+\.\s*", "", trans).strip() for trans in cleaned_translations]
            if len(cleaned_translations) != len(english_sentences_with_timings):
                 print("Error: Fallback sentence count mismatch. Cannot reliably pair translations.")
                 return None # Indicate failure
        
        return cleaned_translations

    except Exception as e:
        print(f"Error during OpenAI API call for translation: {e}")
        return None

def pair_translated_sentences_with_timings(translated_texts_list, original_sentences_with_timings):
    """Pairs translated sentences with their original timings.
    Args:
        translated_texts_list (list): A list of translated sentence strings.
        original_sentences_with_timings (list): The original list of dicts with 'text', 'start', 'end'.
    Returns:
        list: List of dicts, each with translated 'text', and original 'start', 'end'.
    """
    if not translated_texts_list or len(translated_texts_list) != len(original_sentences_with_timings):
        print("Error: Mismatch between translated texts and original sentence timings. Cannot pair.")
        # Attempt to provide more diagnostic info
        print(f"Number of translated texts: {len(translated_texts_list) if translated_texts_list else 0}")
        print(f"Number of original sentences: {len(original_sentences_with_timings)}")
        return [] # Return empty or raise error

    paired_data = []
    for i, translated_text in enumerate(translated_texts_list):
        original_timing = original_sentences_with_timings[i]
        paired_data.append({
            'text': translated_text, # Already cleaned by translate_sentences_to_target_lang
            'start': original_timing['start'],
            'end': original_timing['end']
        })
    print(f"Successfully paired {len(paired_data)} translated sentences with timings.")
    return paired_data


if __name__ == '__main__':
    print("Testing translation.py...")
    if not client:
        print("OpenAI client not initialized (API key likely missing). Skipping translation tests.")
    else:
        print(f"Target language for translation: {config.TARGET_LANGUAGE_NAME} ({config.TARGET_LANGUAGE_CODE})")
        # Example sentences (replace with actual output from transcription for a real test)
        dummy_english_sentences = [
            {'text': "Hello, my name is John. I am 24 years old.", 'start': 0.5, 'end': 4.8},
            {'text': "I have three years of work experience.", 'start': 5.0, 'end': 8.2},
            {'text': "This is a test sentence. What do you think?", 'start': 8.5, 'end': 12.0}
        ]
        print("\nOriginal English Sentences with Timings:")
        for s in dummy_english_sentences:
            print(f"  [{s['start']:.2f}s - {s['end']:.2f}s] {s['text']}")

        translated_strings = translate_sentences_to_target_lang(dummy_english_sentences)

        if translated_strings:
            print(f"\nTranslated {config.TARGET_LANGUAGE_NAME} strings:")
            for i, text in enumerate(translated_strings):
                print(f"  {i+1}. {text}")
            
            paired_hindi_data = pair_translated_sentences_with_timings(translated_strings, dummy_english_sentences)
            
            if paired_hindi_data:
                print(f"\nPaired {config.TARGET_LANGUAGE_NAME} Sentences with Timings:")
                for s_info in paired_hindi_data:
                    print(f"  [{s_info['start']:.2f}s - {s_info['end']:.2f}s] {s_info['text']}")
            else:
                print("Failed to pair translated sentences with timings.")
        else:
            print("Translation failed or returned no results.")

    print("\ntranslation.py test run finished.") 