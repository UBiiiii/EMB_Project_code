from gtts import gTTS
# from IPython.display import Audio
import playsound
# import pygame
from PyQt5  import QtMultimedia
from PyQt5.QtCore  import *
# from PyQt5.

# sound = QtMultimedia.QSoundEffect()

# sound.setSource(QUrl.fromLocalFile("/home/pi/EMB_Project_code/UI_GPIO/sound/hello.mp3"))

# sound.play()
# pygame.mixer.init(frequency=25000)
# pygame.mixer.music.load("/home/pi/EMB_Project_code/source_db/listen.mp3")
# pygame.mixer.music.play()
# while pygame.mixer.music.get_busy() == True:
#     continue

# eng_wav = gTTS(' ', lang = 'ko')
# eng_wav.save('/home/pi/EMB_Project_code/UI_GPIO/sound/space.mp3')
# print('tts done')
playsound.playsound("/home/pi/EMB_Project_code/UI_GPIO/sound/space.mp3")