import os
from cat.mad_hatter.decorators import hook, plugin
from pydantic import BaseModel
from enum import Enum
import subprocess
from datetime import datetime
from threading import Thread
import re
import shlex
from openai import OpenAI

# Settings

# Select box
class VoiceSelect(Enum):
    af_alloy = "af_alloy"
    af_aoede = "af_aoede"
    af_bella = "af_bella"
    af_heart = "af_heart"
    af_jadzia = "af_jadzia"
    af_jessica = "af_jessica"
    af_kore = "af_kore"
    af_nicole = "af_nicole"
    af_nova = "af_nova"
    af_river = "af_river"
    af_sarah = "af_sarah"
    af_sky = "af_sky"
    af_v0 = "af_v0"
    af_v0bella = "af_v0bella"
    af_v0irulan = "af_v0irulan"
    af_v0nicole = "af_v0nicole"
    af_v0sarah = "af_v0sarah"
    af_v0sky = "af_v0sky"
    am_adam = "am_adam"
    am_echo = "am_echo"
    am_eric = "am_eric"
    am_fenrir = "am_fenrir"
    am_liam = "am_liam"
    am_michael = "am_michael"
    am_onyx = "am_onyx"
    am_puck = "am_puck"
    am_santa = "am_santa"
    am_v0adam = "am_v0adam"
    am_v0gurney = "am_v0gurney"
    am_v0michael = "am_v0michael"
    bf_alice = "bf_alice"
    bf_emma = "bf_emma"
    bf_lily = "bf_lily"
    bf_v0emma = "bf_v0emma"
    bf_v0isabella = "bf_v0isabella"
    bm_daniel = "bm_daniel"
    bm_fable = "bm_fable"
    bm_george = "bm_george"
    bm_lewis = "bm_lewis"
    bm_v0george = "bm_v0george"
    bm_v0lewis = "bm_v0lewis"
    ef_dora = "ef_dora"
    em_alex = "em_alex"
    em_santa = "em_santa"
    ff_siwis = "ff_siwis"
    hf_alpha = "hf_alpha"
    hf_beta = "hf_beta"
    hm_omega = "hm_omega"
    hm_psi = "hm_psi"
    if_sara = "if_sara"
    im_nicola = "im_nicola"
    jf_alpha = "jf_alpha"
    jf_gongitsune = "jf_gongitsune"
    jf_nezumi = "jf_nezumi"
    jf_tebukuro = "jf_tebukuro"
    jm_kumo = "jm_kumo"
    pf_dora = "pf_dora"
    pm_alex = "pm_alex"
    pm_santa = "pm_santa"
    zf_xiaobei = "zf_xiaobei"
    zf_xiaoni = "zf_xiaoni"
    zf_xiaoxiao = "zf_xiaoxiao"
    zf_xiaoyi = "zf_xiaoyi"
    zm_yunjian = "zm_yunjian"
    zm_yunxi = "zm_yunxi"
    zm_yunxia = "zm_yunxia"
    zm_yunyang = "zm_yunyang"

class kokoroCatSettings(BaseModel):
    # Select
    base_url: str = "http://host.docker.internal:8880/v1"
    Voice: VoiceSelect = VoiceSelect.af_bella


# Give your settings schema to the Cat.
@plugin
def settings_schema():
    return kokoroCatSettings.schema()


def remove_special_characters(text):
    try:
        # Define the pattern to match special characters excluding punctuation, single and double quotation marks, and Cyrillic characters
        pattern = r'[^a-zA-Z0-9\s.,!?\'"а-яА-Я]'  # Matches any character that is not alphanumeric, whitespace, or specific punctuation, including Cyrillic characters
        
        # Replace special characters with an empty string
        clean_text = re.sub(pattern, '', text)
    except Exception as e:
        print(f"Kokoro Cat plugin: Error occurred cleaning text: {str(e)}")
        clean_text = text
    
    return clean_text

def run_kokoro_process(text, output_filename, cat, base_url, model="kokoro"):
    # Load settings to get the selected voice
    settings = cat.mad_hatter.get_plugin().load_settings()
    selected_voice = settings.get("Voice", VoiceSelect.af_sky)

    try:
        generate_kokoro_speech(text, output_filename, model=model, voice=selected_voice, base_url=base_url)
        kokoro_audio_player = f"<audio controls autoplay><source src='{output_filename}' type='audio/wav'>Your browser does not support the audio tag.</audio>"
        cat.send_ws_message(content=kokoro_audio_player, msg_type='chat')
    except Exception as e:
        print(f"Kokoro Cat plugin: Error occurred: {str(e)}")



# Generate the audio file using the Kokoro API
def generate_kokoro_speech(text, output_file, model="kokoro", voice="af_sky", base_url="http://host.docker.internal:8880/v1"):
    client = OpenAI(base_url=base_url, api_key="not-needed")
    try:
        with client.audio.speech.with_streaming_response.create(
            model=model,
            voice=voice,  
            input=text
        ) as response:
            response.stream_to_file(output_file)
    except Exception as e:
        print(f"Kokoro Cat plugin: Error occurred: {str(e)}")


# Hook function that runs before sending a message
@hook
def before_cat_sends_message(final_output, cat):
    # Get the current date and time
    current_datetime = datetime.now()
    # Format the date and time to use as part of the filename
    formatted_datetime = current_datetime.strftime("%Y%m%d_%H%M%S")
    # Specify the folder path
    folder_path = "/admin/assets/voice"

    # Check if the folder exists, create it if not
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # Construct the output file name with the formatted date and time
    output_filename = os.path.join(folder_path, f"voice_{formatted_datetime}.wav")

    # Get the message sent by LLM
    message = final_output["content"]

    # Load the settings
    settings = cat.mad_hatter.get_plugin().load_settings()
    kokoro_base_url = settings.get("base_url")
    if kokoro_base_url is None:
        kokoro_base_url = "http://host.docker.internal:8880/v1"

    clean_message = remove_special_characters(message)
   
    kokoro_thread = Thread(target=run_kokoro_process, args=(clean_message, output_filename, cat, kokoro_base_url))
    kokoro_thread.start()

    # Return the final output text, leaving kokoro to build the audio file in the background
    return final_output
