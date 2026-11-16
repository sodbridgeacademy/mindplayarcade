
import io
import math
import struct
import wave
import base64

import streamlit as st
import streamlit.components.v1 as components


SOUND_PATTERNS = {
    "click": [(500, 0.10)],
    "correct": [(600, 0.10), (800, 0.14)],
    "wrong": [(300, 0.18), (220, 0.20)],
    "success": [(523, 0.12), (659, 0.12), (784, 0.22)],
    "failure": [(400, 0.15), (300, 0.15), (200, 0.25)],
    "win": [(523, 0.10), (659, 0.10), (784, 0.10), (1047, 0.25)],
    "draw": [(440, 0.12), (440, 0.12)],
}


def generate_sound(pattern):
    sample_rate = 22050
    audio = []

    for frequency, duration in pattern:
        total_samples = int(sample_rate * duration)

        for i in range(total_samples):
            t = i / sample_rate

            fade_in = min(1.0, i / (sample_rate * 0.02))
            fade_out = min(1.0, (total_samples - i) / (sample_rate * 0.04))
            envelope = min(fade_in, fade_out)

            sample = (
                math.sin(2 * math.pi * frequency * t)
                * envelope
                * 0.25
            )

            audio.append(int(sample * 32767))

        audio.extend([0] * int(sample_rate * 0.03))

    buffer = io.BytesIO()

    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)

        frames = b"".join(
            struct.pack("<h", sample) for sample in audio
        )

        wav_file.writeframes(frames)

    return buffer.getvalue()


def play_sound(sound_name):
    if not st.session_state.get("sound_enabled", True):
        return

    pattern = SOUND_PATTERNS.get(sound_name)

    if not pattern:
        return

    audio_data = generate_sound(pattern)
    audio_base64 = base64.b64encode(audio_data).decode("utf-8")

    
    html = f"""
    <!DOCTYPE html>
    <html>
        <body style="margin:0;padding:0;">
            <audio id="game-sound" autoplay>
                <source
                    src="data:audio/wav;base64,{audio_base64}"
                    type="audio/wav"
                >
            </audio>

            <script>
                const audio = document.getElementById("game-sound");
                audio.volume = 0.5;
                audio.play().catch(error => {{
                    console.log("Audio playback was blocked:", error);
                }});
            </script>
        </body>
    </html>
    """


    components.html(
        html,
        height=0,
        scrolling=False,
    )



def queue_sound(sound_name):
    """Save a sound to play after the next Streamlit rerun."""
    st.session_state["pending_sound"] = sound_name


def play_pending_sound():
    """Play a queued sound after the page rerenders."""
    sound_name = st.session_state.pop("pending_sound", None)

    if sound_name:
        play_sound(sound_name)
