from flask import Flask, request, jsonify, send_file
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from werkzeug.utils import secure_filename
import openai
from gtts import gTTS
import os
from pydub import AudioSegment
from pydub.playback import play
import io
import tempfile

app = Flask(__name__)
app.config.from_object('config.Config')
jwt = JWTManager(app)
openai.api_key = app.config['OPENAI_API_KEY']

# Route for user login (for simplicity, no actual user management)
@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    if username == 'user' and password == 'password':  # Dummy authentication
        access_token = create_access_token(identity={'username': username, 'role': 'user'})
        return jsonify(access_token=access_token), 200
    return jsonify({"msg": "Bad username or password"}), 401

# Upload and transcribe audio
@app.route('/transcribe', methods=['POST'])
@jwt_required()
def transcribe():
    if 'audio' not in request.files:
        return jsonify({"msg": "No audio file provided"}), 400

    audio_file = request.files['audio']
    filename = secure_filename(audio_file.filename)
    temp_audio_path = os.path.join(tempfile.gettempdir(), filename)
    audio_file.save(temp_audio_path)

    # Convert audio to text using OpenAI Whisper
    with open(temp_audio_path, "rb") as f:
        transcription = openai.Audio.transcribe("whisper-1", f)

    text = transcription['text']
    
    # Get answer from GPT-4
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=text,
        max_tokens=150
    )
    answer = response.choices[0].text.strip()

    # Convert text to speech using gTTS
    tts = gTTS(text=answer, lang='en')
    temp_audio_response_path = os.path.join(tempfile.gettempdir(), "response.mp3")
    tts.save(temp_audio_response_path)

    return send_file(temp_audio_response_path, mimetype="audio/mp3")

if __name__ == '__main__':
    app.run(debug=True)
