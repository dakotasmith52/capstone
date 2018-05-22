import boto3
from boto3 import Session
from botocore.exceptions import BotoCoreError, ClientError
from contextlib import closing
import os
import sys
import subprocess
from tempfile import gettempdir
import pyaudio

# Create a client using the credentials and region defined in the [adminuser]
# section of the AWS credentials file (~/.aws/credentials).
session = Session(profile_name="default")
polly = session.client("polly")
pollyVoice = {'en': 'Amy', 'fr': 'Celine', 'de': 'Vicki', 'pt': 'Vitoria', 'es':'Miguel'}
languageOptions = {'English': 'en', 'French': 'fr', 'German': 'de', 'Portugese': 'pt', 'Spanish': 'es'}
myfile = input("file to be processed: ")


def mytargetlang():
    while True:
        for key in languageOptions:
            print (key,":",languageOptions[key])
        tlcode = input('please enter the language code: ')
        for key in languageOptions:
            if tlcode != languageOptions[key]:
                continue
            else:
                return tlcode
                break


def readfile(f):
    rf = open(f, 'r')
    txt = rf.read(200)
    return txt


translate = boto3.client(service_name='translate', region_name='us-west-2', use_ssl=True)
result = translate.translate_text(Text=readfile(myfile), 
            SourceLanguageCode='auto', TargetLanguageCode=(mytargetlang()))
# print('TranslatedText: ' + result.get('TranslatedText'))
# print('SourceLanguageCode: ' + result.get('SourceLanguageCode'))
# print('TargetLanguageCode: ' + result.get('TargetLanguageCode'))

targetlanguage = result.get('TargetLanguageCode')


def determineVoice(lang):
    return pollyVoice[lang] if lang in pollyVoice else None


try:
    # Request speech synthesis
    response = polly.synthesize_speech(Text=result.get('TranslatedText'), OutputFormat="mp3",
                                        VoiceId=determineVoice(targetlanguage))
except (BotoCoreError, ClientError) as error:
    # The service returned an error, exit gracefully
    print(error)
    sys.exit(-1)

# Access the audio stream from the response
if "AudioStream" in response:
    # Note: Closing the stream is important as the service throttles on the
    # number of parallel connections. Here we are using contextlib.closing to
    # ensure the close method of the stream object will be called automatically
    # at the end of the with statement's scope.
    with closing(response["AudioStream"]) as stream:
        output = os.path.join(gettempdir(), "speech.wav")

        try:
            # Open a file for writing the output as a binary stream
            with open(output, "wb") as file:
                file.write(stream.read())
        except IOError as error:
            # Could not write to file, exit gracefully
            print(error)
            sys.exit(-1)
else:
    # The response didn't contain audio data, exit gracefully
    print("Could not stream audio")
    sys.exit(-1)

# Play the audio using the platform's default player
if sys.platform == "win32":
    os.startfile(output)
    os.remove(output)
else:
    # the following works on Mac and Linux. (Darwin = mac, xdg-open = linux).
    opener = "open" if sys.platform == "darwin" else "xdg-open"
    subprocess.Popen([opener, output])
    print("I am here")