print("\nImporting a trillion modules...")
requiredModules = {'pyvirtualcam', 'gtts', "opencv-python", "youtube_dl", 
"pydub", "pyautogui", "pygame", "playsound", "numpy"}

try:
    import pyvirtualcam
    import cv2
    import youtube_dl
    import os
    import sys
    from gtts import gTTS
    from io import BytesIO, SEEK_END, SEEK_SET
    from pydub import AudioSegment
    import pyautogui
    import time
    import wave
    from pygame import mixer
    from playsound import playsound
    import requests as rq
    import numpy as np
    import threading
except ImportError:
    print("\nYou forgot to download one or more Python modules in the command prompt using 'pip install MODULE_NAME'")
    print("Required modules:")
    print(requiredModules)
    sys.exit(-1)

# EDIT
keybinds = ["Ctrl", "T"] # push-to-talk keys: https://pyautogui.readthedocs.io/en/latest/quickstart.html
tld = "com" # country domain. check link to full page of accents
lang = "en" # full list of languages and accents:
width, height = 1920, 1080 # camera resolution

# https://stackoverflow.com/a/58763348/14270319
class ResponseStream(object):
    def __init__(self, request_iterator):
        self._bytes = BytesIO()
        self._iterator = request_iterator

    def _load_all(self):
        self._bytes.seek(0, SEEK_END)
        for chunk in self._iterator:
            self._bytes.write(chunk)

    def _load_until(self, goal_position):
        current_position = self._bytes.seek(0, SEEK_END)
        while current_position < goal_position:
            try:
                current_position = self._bytes.write(next(self._iterator))
            except StopIteration:
                break

    def tell(self):
        return self._bytes.tell()

    def read(self, size=None):
        left_off_at = self._bytes.tell()
        if size is None:
            self._load_all()
        else:
            goal_position = left_off_at + size
            self._load_until(goal_position)

        self._bytes.seek(left_off_at)
        return self._bytes.read(size)

    def seek(self, position, whence=SEEK_SET):
        if whence == SEEK_END:
            self._load_all()
        else:
            self._bytes.seek(position, whence)

def load_through_mic(buffer):
    print("Playing through microphone")
    buffer.seek(0)
    mixer.quit() # Quit the mixer as it's initialized on your main playback device
    device = 'CABLE Input (VB-Audio Virtual Cable)'
    mixer.init(devicename=device) # Initialize it with the correct microphone 
    mixer.music.load(buffer)

def convert_audio(audio, format):
    audio.seek(0)
    fp = BytesIO()
    sound = AudioSegment.from_file(audio)
    sound.export(fp, format=format)
    return fp

def generate_voice(text, lang, tld = "com"):
    fp = BytesIO()
    tts = gTTS(text=text, lang=lang, tld = tld)
    
    if os.path.isfile(os.getcwd() + "\\Media Cache\\" + "gtts_audio.mp3"):
        os.remove(os.getcwd() + "\\Media Cache\\" + "gtts_audio.mp3")
    tts.save(os.getcwd() + "\\Media Cache\\gtts_audio.mp3")
    tts.write_to_fp(fp)
    wav_fp = convert_audio(fp, "wav")
    return wav_fp

# stack overflow https://stackoverflow.com/a/44659589/14270319
def image_resize(image, width = None, height = None, inter = cv2.INTER_AREA):
    # initialize the dimensions of the image to be resized and
    # grab the image size
    dim = None
    (h, w) = image.shape[:2]

    # if both the width and height are None, then return the
    # original image
    if width is None and height is None:
        return image

    # check to see if the width is None
    if width is None:
        # calculate the ratio of the height and construct the
        # dimensions
        r = height / float(h)
        dim = (int(w * r), height)

    # otherwise, the height is None
    else:
        # calculate the ratio of the width and construct the
        # dimensions
        r = width / float(w)
        dim = (width, int(h * r))

    # resize the image
    resized = cv2.resize(image, dim, interpolation = inter)

    # return the resized image
    return resized

def play_through_cam(file, width=1920, height=1080, backgroundColor=[0,0,0], fps=False, audioURL=False):
    print("yeet")
    global whenMediaEnds
    cap = cv2.VideoCapture(file)
    VidWidth  = round(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    VidHeight = round(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    if VidWidth > width:
        width = VidWidth
    if VidHeight > height:
        height = VidHeight
    if not fps:
        fps = cap.get(cv2.CAP_PROP_FPS)
    fmt = pyvirtualcam.PixelFormat.BGR # using BGR instead of RGB because that's how OpenCV works

    print("Video loaded. FPS: {0}".format(fps))
    #input("\nPress Enter when you're ready to play. ")
    with pyvirtualcam.Camera(width=width, height=height, fps=fps, fmt=fmt) as cam: # create camera object
        if audioURL:
            pass
        try:
            mixer.music.play()
        except:
            print("No music loaded")
        try:
            while(cap.isOpened()): # Read until video is completed
                ret, frame = cap.read() # Capture frame-by-frame

                if ret:
                    frame = image_resize(frame, height = height)
                    # if height or width of the image is bigger than the
                    # camera width or height then resize it to fit the image
                    if frame.shape[0] > height:
                        frame = cv2.resize(frame, (frame.shape[1], height))
                    if frame.shape[1] > width:
                        frame = cv2.resize(frame, (width, frame.shape[0]))
                    back = np.zeros((height,width,3), np.uint8)
                    backgroundColor.reverse()
                    back[:] = backgroundColor
                    x_offset = round(width / 2 - frame.shape[1] / 2)
                    y_offset = 0
                    back[y_offset:y_offset + frame.shape[0], x_offset:x_offset + frame.shape[1]] = frame
                    cam.send(back)
                    cam.sleep_until_next_frame()
                else:
                    break
        except KeyboardInterrupt:
            print("Stopped video")
            whenMediaEnds = time.time()
        cap.release()

        try:
            mixer.music.stop()
        except:
            pass
        print("\nDone playing")

def change_cam_image(image):
    img = cv2.imread(image)
    imageFit = image_resize(img, height = 1080)
    img_resized = cv2.resize(imageFit, (1920, 1080))

    placeholderPath = os.environ["ProgramFiles"] + r"\obs-studio\data\obs-plugins\win-dshow\placeholder.png"

    if os.path.isfile(placeholderPath):
        cv2.imwrite(placeholderPath, img_resized)
        print("Changed default OBS Studio placeholder image.")
        back = np.zeros((1080,1920,3), np.uint8)
        back[:] = (0, 0, 0)
        fmt = pyvirtualcam.PixelFormat.BGR

        with pyvirtualcam.Camera(width=width, height=height, fps=20, fmt=fmt) as cam:
            cam.send(back)
            cam.sleep_until_next_frame()
    else:
        print("Cannot find OBS Studio placeholder.png path:\n" + placeholderPath)

def fileExists(text):
    for f in os.listdir(os.getcwd()):
        if f.lower() == text.lower():
            return True

def isImageName(text):
    return text.lower().endswith(".png") or text.lower().endswith(".jpg") or text.lower().endswith(".gif") or text.lower().endswith(".jpeg") or text.lower().endswith(".tif") or text.lower().endswith(".tiff")

def show_video():
    print("\nEnter a YouTube video link, the name of an audio or video file, or say something using" +
    "\nthe Google Translate voice, \"tld\" to change the domain of the accent, \"lang\" to" +
    "\nto change the language or voice, \"ptt\" to toggle push to talk.")
    print("\nNote: Make sure the camera isn't launched on the OBS Studio software")
    print("Creating Media Cache folder if it doesn't exist already...")

    if not os.path.isdir("Media Cache"):
        os.mkdir("Media Cache")
    global lang
    global tld
    global whenMediaEnds
    mixer.init()
    whenMediaEnds = time.time() # when media is done playing
    pushToTalk = False

    for fName in os.listdir(os.getcwd() + "\\Media Cache\\"):
        os.remove(os.getcwd() + "\\Media Cache\\" + fName)
    back = np.zeros((1080,1920,3), np.uint8)
    back[:] = (0, 0, 0)
    placeholderPath = os.environ["ProgramFiles"] + r"\obs-studio\data\obs-plugins\win-dshow\placeholder.png"

    if os.path.isfile(placeholderPath):
        cv2.imwrite(placeholderPath, back)
        fmt = pyvirtualcam.PixelFormat.BGR

        with pyvirtualcam.Camera(width=width, height=height, fps=20, fmt=fmt) as cam:
            cam.send(back)
            cam.sleep_until_next_frame()
    while True:
        if time.time() > whenMediaEnds: # waiting for audio or video to finish playing
            if pushToTalk: # if we're using push-to-talk
                for key in keybinds:
                    pyautogui.keyUp(key) # stop push-to-talk because we stopped saying anything
            text = input("\nPlay something: ")
            print("") # add space
            
            if "\n" in text:
                print("Enter key found...")

            if text != "":
                if text.lower() == "lang":
                    lang = input("Enter a new lang: ")
                    continue
                elif text.lower() == "ptt":
                    pushToTalk = not pushToTalk # toggle push to talk
                    print("Push to talk is now " + str(pushToTalk))
                    continue
                elif text.lower() == "tld":
                    tld = input("Enter a new tld: ")
                    continue
                elif fileExists(text):
                    '''
                    if text.endswith(".wav") or text.endswith(".mp3"): # if it's an audio file
                        clip = AudioFileClip(text)
                        whenMediaEnds = time.time() + clip.duration
                        buffer = open(text, "rb").read()
                        load_through_mic(buffer)
                        mixer.music.play()
                        print("Playing audio file for %s seconds." % clip.duration)
                        clip.close()
                    
                    elif
                    '''
                    
                    if isImageName(text):
                        change_cam_image(text)
                    else:
                        # get video duration using fps and frame count
                        cap = cv2.VideoCapture(text)
                        fps = cap.get(cv2.CAP_PROP_FPS)
                        frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                        duration = fps * frames
                        cap.close()

                        whenMediaEnds = time.time() + duration
                        audio = None

                        '''
                        if clip.audio:
                            clip.audio.write_audiofile(os.getcwd() + "\\Media Cache\\extracted_audio.wav")
                            audio = os.getcwd() + "\\Media Cache\\extracted_audio.wav"
                            buffer = open(os.getcwd() + "\\Media Cache\\extracted_audio.wav", "rb")
                            load_through_mic(buffer)
                        else:
                            print("Your video has no audio!")
                        print("Playing video file for %s seconds." % clip.duration) 
                        '''
                        play_through_cam(text, audio=audio)
                        #clip.close()

                elif text.startswith("https") and "www.youtube" in text: # youtube video
                    #video_title = ""

                    ydl_opts = {
                        'format': 'bestvideo[fps=30]+bestaudio', # CHANGE FOR VIDEO
                        'outtmpl': os.getcwd() + "\\Media Cache\\" + "%(title)s.%(ext)s",
                        "writesubtitles": True,
                        'subtitle': '--write-sub --sub-lang en',
                    }
                    print("Downloading YouTube video.")
                    
                    try:
                        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                            info_dict = ydl.extract_info(text, download=False)
                            video_url = info_dict['requested_formats'][0]['url'] 
                            audio_url = info_dict['requested_formats'][1]['url']
                            video_fps = info_dict.get("fps", None)
                    except: # if no 30 FPS frames
                        print("No 30 FPS videos found")
                        ydl_opts["format"] = 'bestvideo+bestaudio'
                        
                        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                            info_dict = ydl.extract_info(text, download=False)
                            video_url = info_dict['requested_formats'][0]['url'] 
                            audio_url = info_dict['requested_formats'][1]['url']
                            video_fps = info_dict.get("fps", None)
                            
                    if type(audio_url) != str:
                        audio_url = False
                    else:
                        r = rq.get(audio_url, stream=True)
                        
                        if r.status_code == 200:
                            stream = ResponseStream(r.iter_content(64))
                            #mixer.music.load(stream)
                            loadingSound = threading.Thread(target=mixer.music.load, args=(stream,))
                            loadingSound.start()
                            print("Music loaded!")
                        else:
                            print("Can't find audio!")
                    print("yeet")
                    play_through_cam(video_url, fps=video_fps, audioURL=audio_url)
                elif text.startswith("http"):
                    r = rq.get(text, stream=True) # get image from url

                    if r.status_code == 200:
                        image_path = os.getcwd() + "\\Media Cache\\" + text.split("/")[-1]
                        f = open(image_path, "w")
                        f.write()
                        f.close()
                        change_cam_image(image_path)
                    else:
                        print("Could not access image:", str(r.status_code))
                else:
                    buffer = generate_voice(text, lang, tld)
                    bufferForLen = BytesIO(buffer.read())
                    
                    with wave.open(bufferForLen) as f:
                        frames = f.getnframes()
                        rate = f.getframerate()
                        duration = frames / float(rate)
                        whenMediaEnds = time.time() + duration
                        print("Playing TTS audio for %s seconds." % duration)
                        f.close()
                    load_through_mic(buffer)
                    mixer.music.play()
                    playsound(os.getcwd() + "\\Media Cache\\gtts_audio.mp3", block=False)

if __name__ == '__main__':
    show_video()