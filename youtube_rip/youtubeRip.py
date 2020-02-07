# Requires youtube-dl CLP to be installed:
# brew install youtube-dl
# and ffmpg:
# brew install ffmpeg
# Also requires an internet connection for youtube download and speech recognition.

import os
import tempfile
import numpy
import soundfile as sf
import speech_recognition as sr
import multiprocessing as mp
import sys
import argparse
from subprocess import call
from pydub import AudioSegment
from datetime import datetime

parser = argparse.ArgumentParser(description='Slice a folder of audio files using fluid-noveltyslice.')
parser.add_argument('-n', '--numsamples', type=int, help='Number of samples to download')
parser.add_argument('-q', '--query', type=str, help='The search term to query youtube with', default='lofi hip hop')
parser.add_argument('-t', '--textcheck', type=bool, help='Check for text (delete sample if not)', default=False)
args = parser.parse_args()

acceptedFiles       = ['.webm', '.wav', '.mp3', '.aiff', '.aif', '.wave', '.m4a']
recursiveMultiplier = 0

#TODO limit number of downloaded tracks
#TODO Folder output

def get_audio(link: str):
    direc = os.path.join(
        os.getcwd(), 'output'
    )
    if not os.path.exists(direc):
        os.makedirs(direc)
    location = direc + '/' + '%(title)s.%(ext)s'

    downloadCommand = [
        'youtube-dl', 
        '-o', location, 
        '-x', '--audio-format', 'wav',
        '--min-filesize', '2.0m',
        '--max-filesize,', '1000.0m',
        '--no-part',
        link
    ]
    call(downloadCommand)

def audio_from_search(searchString: str, pages: int):
    audioLink = 'https://www.youtube.com/results?search_query='

    searchStringList = searchString.split()
    for i in range(len(searchStringList)):
        audioLink = audioLink + searchStringList[i] + "+"

    audioLink = audioLink[:-1] + '&page=' + str(pages)

    get_audio(audioLink)

def convert_audio(file: str):
    src = file
    pre = os.path.splitext(file)[0]
    dst = pre + '.wav'
                                                      
    sound = AudioSegment.from_file(src)
    sound.export(dst, format="wav")

def slice_audio(file: str, **kwargs):
    feature     = kwargs.get('feature',                      '0') # 0=spectrum, 1=MFCC, 2=pitch, 3=loudness
    kernelsize  = kwargs.get('kernelsize',                  '10')
    threshold   = kwargs.get('threshold',                  '0.5')
    filtersize  = kwargs.get('filtersize',                   '1')
    fftsettings = kwargs.get('fftsettings', ['1024', '-1', '-1'])
    createFiles = kwargs.get('createfiles',                 True)

    tmpdir  = tempfile.mkdtemp()
    indices = os.path.join(tmpdir, 'indices.wav')

    processCommand = ['fluid-noveltyslice', '-source', file, '-indices', indices,
                        '-feature', feature, '-kernelsize', kernelsize, '-threshold', threshold,
                        '-filtersize', filtersize, '-fftsettings', fftsettings[0], fftsettings[1], fftsettings[2]]

    print('Slicing audio...')
    call(processCommand)

    data = bufspill(indices)
    originalWav = AudioSegment.from_wav(file)
    print('Found ' + str(len(data) + 1) + ' slices.')

    sfData, samplerate = sf.read(file)

    if createFiles == True:
        print('Exporting slice 1/' + str(len(data) + 1))
        filename = os.path.splitext(file)[0] + '_1.wav'
        originalWav[0 : frame_to_ms(samplerate, data[0])].export(filename, format="wav")
        for i in range(len(data)):
            print('Exporting slice ' + str(i + 2) + '/' + str(len(data) + 1))
            start    = frame_to_ms(samplerate, data[i])
            if i == len(data) - 1:
                end = len(originalWav)
            else:
                end  = frame_to_ms(samplerate, data[i + 1])
            filename = os.path.splitext(file)[0] + '_' + str(i + 2) + '.wav'
            originalWav[start : end].export(filename, format="wav")

def slice_folder(path: str):
    print('Slicing files...')
    fileList = os.listdir(path)
    for i in range(len(fileList)):
        if os.path.splitext(fileList[i])[1] == '.wav':
            name = os.path.join(path, fileList[i])
            slice_audio(name)
            os.remove(name)
            print('Sliced file ' + str(i + 1) + '/' + str(len(fileList)))
    print(str(len(fileList)) + ' files sliced!')

def recursive_slice(path: str, maxLen: float, iteration: int):
    print('Recursive slicing...')
    checkAgain = False
    fileList = os.listdir(path)
    mul = str((1 - (iteration * recursiveMultiplier)) * 0.5)
    for i in range(len(fileList)):
        if os.path.splitext(fileList[i])[1] == '.wav':
            name = path + '/' + fileList[i]
            
            if len(AudioSegment.from_wav(name)) > maxLen * 1000:
                slice_audio(name, threshold=mul)
                os.remove(name)
                checkAgain = True

    if checkAgain == True:
        recursive_slice(path, maxLen, iteration + 1)

def get_speech(file: str):
    r = sr.Recognizer()

    with sr.AudioFile(file) as source:
        #r.adjust_for_ambient_noise(source)
        audio = r.listen(source)
        
        try:
            return r.recognize_google(audio)
        except Exception as e:
            print(e)
            return None

def speech_folder(path: str):
    print('Checking for speech...')
    fileList = os.listdir(path)
    for i in range(len(fileList)):
        if os.path.splitext(fileList[i])[1] == '.wav':
            print('Checking file ' + str(i + 1) + '/' + str(len(fileList)))
            name = path + '/' + fileList[i]
            result = get_speech(name)
            if result is None:
                os.remove(name)
                print('Removed the file: ' + name)
            else:
                print('Found text: ' + result)
    print(str(len(fileList)) + ' files checked!')

def rename_files(path: str):
    print('renaming files...')
    fileList = os.listdir(path)
    for i in range(len(fileList)):
        if os.path.splitext(fileList[i])[1] == '.wav':
            print('Renaming file ' + str(i + 1) + '/' + str(len(fileList)))
            name     = path + '/' + fileList[i]
            fileLen  = str(len(AudioSegment.from_wav(name))).replace('.','_').replace(' ','_').replace(':','_')
            dateTime = str(datetime.now()).replace('.','_').replace(' ','_').replace(':','_')
            newName  = str(i) + '_' + fileLen + '_' + dateTime + '.wav'
            newPath  = path + '/' + newName
            print(newPath)
            os.rename(name, newPath)
            
    print(str(len(fileList)) + ' files renamed!')

def bufspill(audio_file: str):
    try:
        t_data, _ = sf.read(audio_file)
        return t_data.transpose()
    except:
        print(f'Could not read: {audio_file}')

def frame_to_ms(sr: int, frame: int):
    return (frame / sr) * 1000

def full_process(terms: str, textcheck: bool, **kwargs):
    pages  = kwargs.get('pages',1)
    maxlen = kwargs.get('maxlen', 20)
    output_folder = os.path.join(os.getcwd(), 'output')

    audio_from_search(terms, pages)
    slice_folder(output_folder)
    recursive_slice(output_folder, maxlen, 1)
    if textcheck == True:
        speech_folder(output_folder)
    rename_files(output_folder)
    sys.write.stdout('quotes 1')
    print('Finished processing!')

full_process(args.query, args.textcheck)