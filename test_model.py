import pickle
from scipy.io import wavfile
import numpy as np
from scipy import fft
import sklearn
from sklearn.linear_model import LogisticRegression
import os

music_list = ['blues', 'classical', 'country', 'disco', 'hiphop', 'jazz', 'metal', 'pop', 'reggae', 'rock']

file = open("music_model.pkl", "rb")
model = pickle.load(file)
file.close()


for g_index in range(len(music_list)):
    g = music_list[g_index]
    g_path = '../genres/' + g + '/converted/'
    g_files = [f for f in os.listdir(g_path) if os.path.isfile(os.path.join(g_path, f))]
    for file in g_files:
        full_file_path = os.path.join(g_path, file)
        if file.endswith('.mp3'):
            wav_path = '.\\train_converted\\' + os.path.basename(file)[:-4] + '.wav'
            if not os.path.exists(wav_path):
                print(wav_path, 'not found')
                continue
        else:
            wav_path = full_file_path
        try:
            sample_rate, X = wavfile.read(wav_path)
            if len(X.shape) > 1:
                X = X[:, 0]
        except Exception as e:
            print('Wav read error!' + str(e))
            continue
        X = abs(fft(X)[:1000])
        X = np.array(X).reshape(1, -1)
        # print(model)
        y = model.predict(X)
        # print(y)
        if y != g_index:
            print('g', g_index, 'y', y)
        # print(music_list[y[0]])
    print('g_index', g_index, 'ok')
