from flask import Flask, request, jsonify
from flask_cors import CORS
from google.cloud import speech_v1 as speech
from google.cloud import translate_v2 as translate
from pydub import AudioSegment
from textblob import TextBlob
import wave
import os
import time

app = Flask(__name__)
CORS(app)

# Google Cloud clients
speech_client = speech.SpeechClient.from_service_account_file('/home/kaved/Downloads/key.json')
translate_client = translate.Client.from_service_account_json('/home/kaved/Downloads/key.json')

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

    # Speech-to-text timing
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

    # Translation timing
    translation_start = time.time()
    translations = {}
    for lang in languages:
        result = translate_client.translate(transcript, target_language=lang)
        translations[lang] = f"\n[{lang}]\n{result['translatedText']}"
    translation_end = time.time()

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

    # Cleanup
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
