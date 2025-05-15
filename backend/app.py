from flask import Flask, request, jsonify, url_for
from flask_cors import CORS
from google.cloud import speech_v1 as speech
from google.cloud import translate_v2 as translate
from pydub import AudioSegment
from textblob import TextBlob
from gtts import gTTS
import wave
import os
import time
import uuid

app = Flask(__name__)
CORS(app)

# Google Cloud clients
speech_client = speech.SpeechClient.from_service_account_file('/home/kaved/Downloads/key.json')
translate_client = translate.Client.from_service_account_json('/home/kaved/Downloads/key.json')

# TTS output folder
TTS_FOLDER = os.path.join(app.root_path, 'static', 'tts')
os.makedirs(TTS_FOLDER, exist_ok=True)

def convert_to_mono(input_path, output_path):
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1)
    audio.export(output_path, format="wav")

def get_star_rating(polarity):
    if polarity >= 0.6:
        return "⭐⭐⭐⭐⭐ (Very Positive)"
    elif polarity >= 0.2:
        return "⭐⭐⭐ (Positive)"
    elif polarity > -0.2:
        return "⭐⭐⭐ (Neutral)"
    elif polarity > -0.6:
        return "⭐⭐ (Negative)"
    else:
        return "⭐ (Very Negative)"

def generate_tts(text, lang_code):
    tts = gTTS(text=text, lang=lang_code)
    filename = f"tts_{uuid.uuid4().hex}.mp3"
    filepath = os.path.join(TTS_FOLDER, filename)
    tts.save(filepath)
    audio_url = url_for('static', filename=f'tts/{filename}', _external=True)
    return audio_url

@app.route('/upload', methods=['POST'])
def upload():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files['audio']
    languages = request.form.getlist('languages')

    audio_path = 'temp_audio.wav'
    mono_path = 'mono_audio.wav'
    audio_file.save(audio_path)
    convert_to_mono(audio_path, mono_path)

    with wave.open(mono_path, "rb") as wav_file:
        sample_rate = wav_file.getframerate()

    # Speech-to-text
    stt_start = time.time()
    with open(mono_path, 'rb') as f:
        content = f.read()
        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=sample_rate,
            language_code='en-US',
        )
        response = speech_client.recognize(config=config, audio=audio)
    stt_end = time.time()

    transcript = ""
    for result in response.results:
        if result.alternatives:
            transcript += result.alternatives[0].transcript + " "
    transcript = transcript.strip()

    # Translation + TTS
    translation_start = time.time()
    translations = {}
    for lang in languages:
        result = translate_client.translate(transcript, target_language=lang)
        translated_text = result['translatedText']
        audio_url = generate_tts(translated_text, lang.lower())
        translations[lang] = {
            "text": translated_text,
            "audio": audio_url
        }
    translation_end = time.time()

    # Sentiment analysis
    sentiment_start = time.time()
    blob = TextBlob(transcript)
    polarity = blob.sentiment.polarity
    subjectivity = blob.sentiment.subjectivity
    sentiment = {
        "polarity": polarity,
        "subjectivity": subjectivity,
        "rating": get_star_rating(polarity)
    }
    sentiment_end = time.time()

    # Cleanup temporary files
    os.remove(audio_path)
    os.remove(mono_path)

    return jsonify({
        "transcript": transcript,
        "translations": translations,
        "sentiment": sentiment,
        "performance": {
            "speech_to_text_seconds": round(stt_end - stt_start, 2),
            "translation_seconds": round(translation_end - translation_start, 2),
            "sentiment_analysis_seconds": round(sentiment_end - sentiment_start, 2)
        }
    })

if __name__ == '__main__':
    app.run(debug=True)
