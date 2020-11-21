import matplotlib
matplotlib.use('Qt5Agg')
from PyQt5.QtWidgets import QVBoxLayout, QSizePolicy, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.animation as animation
from scipy.io import wavfile
from threading import Lock
import os

CHUNK = 50


class MyCanvas(FigureCanvas):
    def __init__(self, parent=None):
        plt.rcParams['font.family'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False

        self.fig = plt.figure()
        self.fig.set_facecolor("#f0f0f0")
        plt.axis('off')

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        '''定义FigureCanvas的尺寸策略，这部分的意思是设置FigureCanvas，使之尽可能的向外填充空间。'''
        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)


class WaveWidget(QWidget):
    def __init__(self, parent=None):
        super(WaveWidget, self).__init__(parent)
        self.layout = QVBoxLayout(self)
        self.my_canvas = MyCanvas(self)
        self.layout.addWidget(self.my_canvas)
        self.my_canvas.fig.suptitle('')
        self.my_canvas.hide()

        self.ani = None
        self.sample_rate = 8000
        self.X = []
        self.mutex = Lock()
        self.cur_play_time = 0  # time in milliseconds

        self.bar_collections = []
        for i in range(4):
            def _get_bar_list(x_len):
                return [15000] * x_len
            self.bar_collections.append(plt.bar(range(CHUNK * 2), _get_bar_list(CHUNK * 2)))

    def load_file(self, filename):
        wav_name = '.\\converted\\' + os.path.basename(filename)[:-4] + '.wav'
        if not os.path.exists(wav_name):
            import subprocess
            subprocess.run(['.\\bin\\ffmpeg.exe', '-y', '-i', filename, '-ar', '8000', wav_name])
        self.sample_rate, X = wavfile.read(wav_name)
        if len(X.shape) == 1:
            self.X = np.array(X)
        else:
            self.X = np.array(X)[:, 0]
        self.cur_play_time = 0
        self.stop_audio()

    def set_cur_play_time(self, cur_play_time):
        self.mutex.acquire()
        self.cur_play_time = cur_play_time
        self.mutex.release()

    def start_audio(self, *args, **kwargs):
        self.ani = animation.FuncAnimation(self.my_canvas.fig, self.plot_update,
                                           interval=100,
                                           blit=False,
                                           repeat=False)

        self.my_canvas.draw()

    def plot_update(self, i):
        self.my_canvas.show()
        self.mutex.acquire()
        cur_time_index = int(self.cur_play_time * self.sample_rate / 1000)
        self.mutex.release()
        min_index = cur_time_index - CHUNK
        max_index = cur_time_index + CHUNK
        if min_index < 0:
            min_index = 0
        elif max_index >= self.X.shape[0]:
            max_index = self.X.shape[0] - 1
            min_index = max_index - 2 * CHUNK

        for i in range(CHUNK * 2):
            height = self.X[min_index + i]
            height_min = 1000
            self.bar_collections[0][i].set_height(height + height_min * 2)
            self.bar_collections[0][i].set_color('wheat')
            self.bar_collections[1][i].set_height(height / 2 + height_min * 1.5)
            self.bar_collections[1][i].set_color('gold')
            self.bar_collections[2][i].set_height(height / 3 + height_min * 1.2)
            self.bar_collections[2][i].set_color('darkorange')
            self.bar_collections[3][i].set_height(height / 8 + height_min)
            self.bar_collections[3][i].set_color('red')

    def pause_audio(self):
        if self.ani:
            self.ani.event_source.stop()
        self.ani = None

    def stop_audio(self):
        self.pause_audio()
        self.my_canvas.hide()
