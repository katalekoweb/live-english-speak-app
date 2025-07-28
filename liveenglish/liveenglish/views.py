from django.shortcuts import render
from django.http import JsonResponse
import asyncio
from edge_tts import Communicate
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import speech_recognition as sr
from pydub import AudioSegment
import tempfile
import os
from openai import OpenAI
client = OpenAI(
    api_key="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"
)

async def text_to_audio(text, output_file, voice="en-US-AriaNeural"):
    communicate = Communicate(text, voice)
    await communicate.save(output_file)

def home(request):
    return render(request, 'home.html')

def get_gpt_answer (request):
    text = request.GET.get("text")
    conversation = []

    if text:
        conversation.append({"role": "user", "content": text})

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation,
            stream=False,
        )

        assistant_reply = response.choices[0].message.content
        return JsonResponse({"reply": assistant_reply})


def generate_audio(request):
    text = request.GET.get("text", "Hello, this is a test of Edge TTS.")
    print(text)
    audio_filename = "output.mp3"
    audio_path = os.path.join("media", audio_filename)

    # Generate audio if not exists or text changed
    if not os.path.exists(audio_path) or request.GET.get("text"):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(text_to_audio(text, audio_path))

    audio_url = f"/media/{audio_filename}"
    return JsonResponse({"audio_url": audio_url, "text": text})

@csrf_exempt
def extract_text(request):
    if request.method == 'POST' and request.FILES.get('audio'):
        audio_file = request.FILES['audio']
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_audio:
            for chunk in audio_file.chunks():
                temp_audio.write(chunk)
            temp_audio_path = temp_audio.name

        # Convert webm to wav (SpeechRecognition needs wav)
        wav_path = temp_audio_path.replace('.webm', '.wav')
        sound = AudioSegment.from_file(temp_audio_path)
        sound.export(wav_path, format="wav")

        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio)
            except sr.UnknownValueError:
                text = ""
            except sr.RequestError:
                text = ""

        os.remove(temp_audio_path)
        os.remove(wav_path)
        return JsonResponse({'text': text})
    return JsonResponse({'error': 'No audio file received'}, status=400)
