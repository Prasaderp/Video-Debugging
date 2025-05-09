import os
from moviepy.editor import VideoFileClip, AudioFileClip
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
import config

def replace_audio_in_video(original_video_path, new_audio_path, final_video_output_path):
    print(f"Loading original video: {original_video_path}")
    video_clip = VideoFileClip(original_video_path)
    
    print(f"Loading new audio: {new_audio_path}")
    new_audio_clip = AudioFileClip(new_audio_path)
    
    print("Setting new audio to video clip...")
    final_video_clip = video_clip.set_audio(new_audio_clip)
    
    os.makedirs(os.path.dirname(final_video_output_path), exist_ok=True)

    print(f"Writing final video to: {final_video_output_path}")
    try:
        final_video_clip.write_videofile(
            final_video_output_path,
            codec=config.OUTPUT_VIDEO_CODEC,
            audio_codec=config.OUTPUT_AUDIO_CODEC,
            verbose=True,
            logger='bar'
        )
        print(f"Final video saved successfully to: {final_video_output_path}")
    except Exception as e:
        print(f"Error writing final video: {e}")
        if os.path.exists(final_video_output_path):
            try:
                os.remove(final_video_output_path)
                print(f"Removed partially written file: {final_video_output_path}")
            except Exception as e_rem:
                print(f"Error removing partially written file: {e_rem}")
        raise
    finally:
        if 'video_clip' in locals() and video_clip:
            video_clip.close()
        if 'new_audio_clip' in locals() and new_audio_clip:
            new_audio_clip.close()
        if 'final_video_clip' in locals() and final_video_clip and hasattr(final_video_clip, 'close'):
            final_video_clip.close()

    return final_video_output_path

if __name__ == '__main__':
    print("Testing video_processing.py...")

    test_original_video_path = os.path.join(config.VIDEO_DIR, "test_video.mp4")
    test_new_audio_path = os.path.join(config.SYNCHRONIZED_AUDIO_DIR, "test_synchronized_output.wav")
    test_final_output_dir = os.path.join(config.OUTPUT_VIDEO_DIR, "test_output")
    test_final_video_path = os.path.join(test_final_output_dir, "test_video_final_processed.mp4")

    if not os.path.exists(test_original_video_path):
        print(f"Original test video not found: {test_original_video_path}. Run audio_processing.py tests first.")
    elif not os.path.exists(test_new_audio_path):
        print(f"Test synchronized audio not found: {test_new_audio_path}. Run audio_processing.py tests first.")
    else:
        print(f"Using original video: {test_original_video_path}")
        print(f"Using new audio: {test_new_audio_path}")
        replace_audio_in_video(test_original_video_path, test_new_audio_path, test_final_video_path)
        print(f"Test processed video should be at: {test_final_video_path}")

    print("video_processing.py test run finished.") 