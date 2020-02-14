# Requires youtube-dl CLP to be installed:
# brew install youtube-dl
# and ffmpg:
# brew install ffmpeg
# Also requires an internet connection for youtube download and speech recognition.

verbose = True
if verbose:
    print('Starting youtube rip')

import os
import tempfile
import numpy
import soundfile as sf
import speech_recognition as sr
import multiprocessing as mp
import argparse
import subprocess
from pydub import AudioSegment
from datetime import datetime
from typing import List

FFTConfig = List[str]

#Utility for better command line arg parsing for booleans
def str2bool(v):
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

parser = argparse.ArgumentParser(description='Slice a folder of audio files using fluid-noveltyslice.')
parser.add_argument('-n', '--numsamples', type=int, help='Number of samples to download', default=1)
parser.add_argument('-q', '--query', type=str, help='The search term to query youtube with', default='lofi hip hop')
parser.add_argument('-t', '--textcheck', type=str2bool, help='Check for text (delete sample if not)', default=False)
parser.add_argument('-o', '--output', type=str, help='Output folder', default=os.path.join(os.getcwd(), 'output'))
parser.add_argument('-r', '--recursive', type=str2bool, help='Boolean for determining if slicing should be performed recursively', default=True)
parser.add_argument('-i', '--iterations', type=int, help='Number of iterations to recursively slice.', default=1)
parser.add_argument('-m', '--maxlen', type=int, help='Maximum length to recursively slice to.', default=20)
parser.add_argument('-p', '--numpages', type=int, help='Number of youtube pages to scrape', default=1)
parser.add_argument('-x', '--randomsearch', type=str2bool, help='Randomly scramble the search indices', default=True)
parser.add_argument('-s', '--minsize', type=int, help='The minimum size of a returned file.', default=100)
args = parser.parse_args()

acceptedFiles       = ['.webm', '.wav', '.mp3', '.aiff', '.aif', '.wave', '.m4a']
recursiveMultiplier = 0

#TODO limit number of downloaded tracks
#TODO Folder output

class YoutubeQuery():
    """
    YoutubeQuery is a container for all the functions and data required to request and download videos from youtube
    """
    def __init__(self):
        self.numsamples:int
        self.output:str
        self.query:str
        self.recognise_speech:bool
        self.slice_recursively:bool
        self.num_pages:int
        self.recursion_params:dict
        self.random_search:bool
        self.minslice:int

    def bufspill(self, audio_file: str):
        try:
            t_data, _ = sf.read(audio_file)
            return t_data.transpose()
        except:
            print(f'Could not read: {audio_file}')

    def frame_to_ms(self, sr: int, frame: int):
        return (frame / sr) * 1000

    def audio_from_search(self, pages: int):
        audio_link = 'https://www.youtube.com/results?search_query='

        if verbose:
            print('Searching youtube for: ' + self.query)

        search_string_list = self.query.split()
        for i in range(len(search_string_list)):
            audio_link = audio_link + search_string_list[i] + "+"

        audio_link = audio_link[:-1] + '&page=' + str(pages)

        if not os.path.exists(args.output):
            os.makedirs(args.output)
            if verbose:
                print('Creating output file here: ' + args.output)
        location = args.output + '/' + '%(title)s.%(ext)s'

        numsamples = self.numsamples
        random_search = self.random_search

        subprocess_args = [
            'youtube-dl', 
            '-o', location, 
            '-x', '--audio-format', 'wav',
            '--max-downloads', str(numsamples),
            '--no-part',
            '--playlist-random',
            '--match-filter', '!is_live',
            audio_link
        ]

        #Remove the one before the last entry, which is '--playlist-random'
        if not random_search:
            del subprocess_args[len(subprocess_args) - 2]
        
        print('TEST')
        subprocess.call(subprocess_args, shell=False)
        if verbose:
                print('Youtube-dl subprocess completed.')

    def slice_audio(
        self, 
        file:str, 
        feature:str="0",
        kernelsize:str="10",
        threshold:str="0.5",
        filtersize:str="1",
        fftsettings:FFTConfig=['1024', '-1', '-1'],
        create_files:bool=True):

        tmpdir  = tempfile.mkdtemp()
        indices = os.path.join(tmpdir, 'indices.wav')

        processCommand = ['fluid-noveltyslice', '-source', file, '-indices', indices,
                            '-feature', feature, '-kernelsize', kernelsize, '-threshold', threshold,
                            '-filtersize', filtersize, '-fftsettings', fftsettings[0], fftsettings[1], fftsettings[2]]

        print('Slicing audio...')
        subprocess.call(processCommand)

        data = self.bufspill(indices)
        originalWav = AudioSegment.from_wav(file)
        print('Found ' + str(len(data) + 1) + ' slices.')

        sfData, samplerate = sf.read(file)

        if create_files == True:
            print('Exporting slice 1/' + str(len(data) + 1))
            filename = os.path.splitext(file)[0] + '_1.wav'
            originalWav[0 : self.frame_to_ms(samplerate, data[0])].export(filename, format="wav")
            for i in range(len(data)):
                print('Exporting slice ' + str(i + 2) + '/' + str(len(data) + 1))
                start    = self.frame_to_ms(samplerate, data[i])
                if i == len(data) - 1:
                    end = len(originalWav)
                else:
                    end  = self.frame_to_ms(samplerate, data[i + 1])
                filename = os.path.splitext(file)[0] + '_' + str(i + 2) + '.wav'
                originalWav[start : end].export(filename, format="wav")

    def slice_folder(self):
        print('Slicing files...')
        file_list = os.listdir(self.output)
        for i in range(len(file_list)):
            if os.path.splitext(file_list[i])[1] == '.wav':
                name = os.path.join(self.output, file_list[i])
                self.slice_audio(file=name)
                os.remove(name)
                print('Sliced file ' + str(i + 1) + '/' + str(len(file_list)))
        print(str(len(file_list)) + ' files sliced!')

        self.delete_small_files()

    def delete_small_files(self):
        print('Deleting files that are too small...')
        file_list = os.listdir(self.output)
        for i in range(len(file_list)):
            if os.path.splitext(file_list[i])[1] == '.wav':
                name = name = self.output + '/' + file_list[i]
                if os.path.getsize(name) < self.minsize:
                    os.remove(name)
                    print('Deleted ' + name)
                
    def recursive_slice(self, iterations=1):
        print('Recursive slicing...')
        checkAgain = False
        file_list = os.listdir(self.output)
        mul = str((1 - (iterations * recursiveMultiplier)) * 0.5)
        for i in range(len(file_list)):
            if os.path.splitext(file_list[i])[1] == '.wav':
                name = self.output + '/' + file_list[i]
    
                if len(AudioSegment.from_wav(name)) > self.recursion_params["maximum_length"] * 1000:
                    self.slice_audio(name, threshold=mul)
                    os.remove(name)
                    checkAgain = True

        self.delete_small_files()

        if checkAgain == True:
            self.recursive_slice(iterations=iterations+1)

    def get_speech(self, file: str):
        r = sr.Recognizer()

        with sr.AudioFile(file) as source:
            #r.adjust_for_ambient_noise(source)
            audio = r.listen(source)
            
            try:
                return r.recognize_google(audio)
            except Exception as e:
                print(e)
                return None

    def speech_folder(self):
        print('Checking for speech...')
        file_list = os.listdir(self.output)
        for i in range(len(file_list)):
            if os.path.splitext(file_list[i])[1] == '.wav':
                print('Checking file ' + str(i + 1) + '/' + str(len(file_list)))
                name = path + '/' + file_list[i]
                result = get_speech(name)
                if result is None:
                    os.remove(name)
                    print('Removed the file: ' + name)
                else:
                    print('Found text: ' + result)
        print(str(len(file_list)) + ' files checked!')

    def rename_files(self):
        print('renaming files...')
        file_list = os.listdir(self.output)
        for i in range(len(file_list)):
            if os.path.splitext(file_list[i])[1] == '.wav':
                print('Renaming file ' + str(i + 1) + '/' + str(len(file_list)))
                name     = path + '/' + file_list[i]
                fileLen  = str(len(AudioSegment.from_wav(name))).replace('.','_').replace(' ','_').replace(':','_')
                dateTime = str(datetime.now()).replace('.','_').replace(' ','_').replace(':','_')
                newName  = str(i) + '_' + fileLen + '_' + dateTime + '.wav'
                newPath  = path + '/' + newName
                print(newPath)
                os.rename(name, newPath)
                
        print(str(len(file_list)) + ' files renamed!')
    
    def info_to_max(self):
        print('Some return information to max about where le files are')


# Creat the class instance
scraper = YoutubeQuery()
# Setup parameters
scraper.numsamples = args.numsamples
scraper.output = args.output
scraper.query = args.query
scraper.num_pages = args.numpages
scraper.recognise_speech = args.textcheck
scraper.slice_recursively = args.recursive
scraper.random_search = args.randomsearch
scraper.recursion_params = {
    "maximum_length" : args.maxlen
}
scraper.minsize = args.minsize

# This could be wrapped up in a process() function which knows which bits to do
if verbose:
    print('Getting audio from search...')
scraper.audio_from_search(pages=3)
if verbose:
    print('Slicing...')
scraper.slice_folder()


if scraper.slice_recursively:
    if verbose:
        print('Slicing recursively...')
    scraper.recursive_slice()
if scraper.recognise_speech:
    if verbose:
        print('Checking for speech...')
    scraper.speech_folder() # <<-- Optional

if verbose:
    print('Renaming files...')
scraper.rename_files()
scraper.info_to_max()

