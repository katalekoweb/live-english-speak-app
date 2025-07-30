from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
import asyncio
from edge_tts import Communicate
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import speech_recognition as sr
from pydub import AudioSegment
import tempfile
import os
from openai import OpenAI
from django.contrib.auth.decorators import login_required
from users.models import Message
from django.db.models import Q

client = OpenAI(
    api_key="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"
)

async def text_to_audio(text, output_file, voice="en-US-AriaNeural"):
    communicate = Communicate(text, voice)
    await communicate.save(output_file)

@login_required
def home(request):
    user = request.user
    messages = Message.objects.filter(Q(sender=user) | Q(recipient=user)).order_by('-id')

    if messages.__len__() == 0:
        # train the prompt to an english teacher
        conversationTrain = []
        train_message = "You are my english teacher. Always give me short answers. Always that we are talking if i make a mistake please correct me"
        conversationTrain.append({"role": "user", "content": train_message})

        # save to the database
        message = Message()
        message.sender = request.user
        message.content = train_message
        message.save()

        # return JsonResponse({'messages', conversation})
        responseTrain = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversationTrain,
            stream=False,
        )

        # store the answer from gpt ai
        assistant_reply_train = responseTrain.choices[0].message.content
        if assistant_reply_train is not None:
            message = Message()
            message.recipient = request.user
            message.content = assistant_reply_train
            message.save()

        # get messages again
        messages = Message.objects.filter(Q(sender=user) | Q(recipient=user)).order_by('-id')

    # return HttpResponse(messages.__len__())

    conversation = []
    # Convert to list of dicts
    for msg in messages:
        conversation.append({
            # 'id': msg.id,
            # 'sender': msg.sender.username if msg.sender else None,
            # 'recipient': msg.recipient.username if msg.recipient else None,
            'role': 'user' if msg.sender else 'assistant', 
            'content': msg.content,
            # 'created_at': msg.created_at.isoformat(),
        })

    print(conversation)

    return render(request, 'home.html')

def get_gpt_answer (request):
    text = request.GET.get("text")
    conversation = []
    assistant_reply = ""

    # remove all messages
    # Message.objects.all().delete()
    # return HttpResponse("Messages deletes")

    # get message from the user
    user = request.user
    messages = Message.objects.filter(Q(sender=user) | Q(recipient=user)).order_by('-id')

  
    # Convert to list of dicts
    for msg in messages:
        conversation.append({
            # 'id': msg.id,
            # 'sender': msg.sender.username if msg.sender else None,
            # 'recipient': msg.recipient.username if msg.recipient else None,
            'role': 'user' if msg.sender else 'assistant', 
            'content': msg.content,
            # 'created_at': msg.created_at.isoformat(),
        })

    if text:
        conversation.insert(0, {"role": "user", "content": text})
        conversation.append({"role": "user", "content": text})

        # save to the database
        message = Message()
        message.sender = request.user
        message.content = text
        message.save()

        # return JsonResponse({'messages', conversation})

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation,
            stream=False,
        )

        conversation.pop()

        assistant_reply = response.choices[0].message.content

        if assistant_reply is not None:
            message = Message()
            message.recipient = request.user
            message.content = assistant_reply
            message.save()
            # save to list
            conversation.insert(0, {"role": "assistant", "content": assistant_reply})

    return JsonResponse({"reply": assistant_reply, 'messages': conversation})


def generate_audio(request):
    text = request.GET.get("text", "Hello, this is a test of Edge TTS.")
    text = text.replace("*", "")
    text = text.replace("#", "")

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
