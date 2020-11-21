from scipy.io import wavfile
import numpy as np
from scipy import fft
import os
from sklearn.linear_model import LogisticRegression
import pickle
import subprocess

music_list = ['blues', 'classical', 'country', 'disco', 'hiphop', 'jazz', 'metal', 'pop', 'reggae', 'rock']

X = []
y = []

for g in music_list:
    g_path = '../genres/' + g + '/converted/'
    g_files = [f for f in os.listdir(g_path) if os.path.isfile(os.path.join(g_path, f))]
    for file in g_files:
        print(file)
        full_file_path = os.path.join(g_path, file)
        if file.endswith('.mp3'):
            wav_path = '.\\train_converted\\' + os.path.basename(file)[:-4] + '.wav'
            if not os.path.exists(wav_path):
                try:
                    subprocess.run(['.\\bin\\ffmpeg.exe', '-y', '-i', full_file_path, '-ar', '8000', wav_path])
                except Exception as e:
                    print('Convert error!' + str(e))
                    continue
        else:
            wav_path = full_file_path
        try:
            sample, x = wavfile.read(wav_path)
            if len(x.shape) > 1:
                x = x[:, 0]
        except Exception as e:
            print('Wav read error!' + str(e))
            continue
        fft_features = abs(fft(x)[:1000])
        X.append(fft_features)
        y.append(music_list.index(g))
    print('ddd')

X = np.array(X)
y = np.array(y)

lr_model = LogisticRegression()
lr_model.fit(X, y)
file = open('music_model.pkl', 'wb')
pickle.dump(lr_model, file)
file.close()
