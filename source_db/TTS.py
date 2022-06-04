from gtts import gTTS
# from IPython.display import Audio
import playsound

eng_wav = gTTS('길찾기 기능을 이용하시려면 선택 버튼을 눌러주세요', lang = 'ko')
eng_wav.save('eng.mp3')
print('tts done')
playsound.playsound('eng.mp3')