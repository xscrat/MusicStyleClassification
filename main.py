from PyQt5.QtCore import Qt, QUrl, QSize, QThread
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import (QApplication, QDialog, QFileDialog, QHBoxLayout, QListWidgetItem, QSlider,
                             QStyle, QTableWidgetItem, QFrame)
from PyQt5.QtWidgets import QMainWindow, QPushButton, QAction, QHeaderView
from PyQt5.QtGui import QIcon, QColor, QFont
import sys
import os
import random
import math
import time
from main_window import Ui_MainWindow
from my_popup import Ui_Dialog
from songs_data import SongsDataManager
import pickle
from scipy.io import wavfile
import numpy as np
from scipy import fft
import globals
from PyQt5.QtCore import pyqtSignal
import subprocess
import shutil


class ProcessingFilesThread(QThread):
    def __init__(self, parent=None, main_widget=None, names=[]):
        super(ProcessingFilesThread, self).__init__(parent)
        self.main_widget = main_widget
        self.names = names

    def run(self):
        file_to_style_dict = {}
        has_error = False

        for name in self.names:
            try:
                if name.endswith('.mp3') or name.endswith('.wav'):
                    wav_name = '.\\converted\\' + os.path.basename(name)[:-4] + '.wav'
                    subprocess.run(['.\\bin\\ffmpeg.exe', '-y', '-i', name, '-ar', '8000', wav_name])
                else:
                    raise Exception('unsupported format')
                sample_rate, x = wavfile.read(wav_name)
                if len(x.shape) > 1:
                    x = x[:, 0]
                if x.shape[0] / sample_rate < 10:
                    raise Exception('歌曲长度少于10秒')
                x = abs(fft(x)[:1000])
                x = np.array(x).reshape(1, -1)
                y = self.main_widget.model.predict(x)[0]
                if 0 <= y < len(globals.styles) - 1:
                    file_to_style_dict[name] = y
                else:
                    file_to_style_dict[name] = len(globals.styles) - 1
            except Exception as e:
                has_error = True
                err_str = '导入失败' + os.linesep + os.path.basename(name) + ': ' + str(e)
                break

        while_count = 0
        while True:
            time.sleep(1)
            if hasattr(self.main_widget, 'progress_window'):
                if self.main_widget.progress_window.isActiveWindow():
                    break
            while_count += 1
            if while_count == 10:
                break

        if has_error:
            self.main_widget.detected_result_str = err_str
            self.main_widget.signal_close_popup.emit()
            return

        name_to_style_dict = {}
        for name in self.names:
            style = globals.styles[file_to_style_dict[name]]
            name_to_style_dict[name] = style
            self.main_widget.songs_data.setdefault(style, {})
            if name not in self.main_widget.songs_data[style]:
                self.main_widget.songs_data[style].setdefault(name, {})

        self.main_widget.songs_data_manager.write_songs_data(self.main_widget.songs_data)
        self.main_widget.detected_result_str = ''
        for name, style in name_to_style_dict.items():
            self.main_widget.detected_result_str += os.path.basename(name) + '已被识别为' +\
                                        globals.styles_chinese[globals.styles.index(style)] + os.linesep

        self.main_widget.signal_close_popup.emit()


class MyPopup(QDialog, Ui_Dialog):
    def __init__(self, has_close=False, main_widget=None):
        QDialog.__init__(self)
        Ui_Dialog.__init__(self)
        self.setupUi(self)
        self.setWindowTitle(' ')
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        if not has_close:
            self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.setWindowModality(Qt.ApplicationModal)
        if main_widget:
            main_widget.signal_close_popup.connect(self.on_close_signal_received)

    def on_close_signal_received(self):
        self.close()


class MyMainForm(QMainWindow, Ui_MainWindow):
    signal_close_popup = pyqtSignal()

    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)

        self.setWindowTitle(' ')
        self.setWindowFlags(Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint | Qt.MSWindowsFixedSizeDialogHint)

        self.songs_data_manager = SongsDataManager()
        self.songs_data = self.songs_data_manager.read_songs_data()

        self.column_num = 2
        self.row_num = math.ceil(globals.style_num / self.column_num)

        self._generate_colors(globals.style_num)

        self.action = QAction('导入')
        self.main_menu.addAction(self.action)
        self.action.triggered.connect(self._import_files)

        self.styles_widget.load_styles_images()

        self.style_table_widget.setVisible(False)
        self.style_table_widget.setShowGrid(False)
        self.style_table_widget.setFrameShape(QFrame.NoFrame)
        self.style_table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.style_table_widget.horizontalHeader().setVisible(False)
        self.style_table_widget.verticalHeader().setVisible(False)
        self.style_table_widget.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.style_table_widget.setColumnCount(self.column_num)
        self.style_table_widget.setRowCount(self.row_num)

        self.table_items = []
        self.playlist_items = []
        self.selected_style_index = -1
        self.selected_song_name = ''
        self.location_root = os.getcwd()

        for i in range(self.row_num * self.column_num):
            row = math.floor(i / self.column_num)
            column = math.floor(i % self.column_num)
            if i < globals.style_num:
                table_item = QTableWidgetItem(globals.styles_chinese[i])
                table_item.setData(Qt.FontRole, QFont("", 20))
                table_item.setBackground(self.qcolors[i])
            else:
                table_item = QTableWidgetItem('')
            self.table_items.append(table_item)
            table_item.setTextAlignment(Qt.AlignCenter)
            self.style_table_widget.setItem(row, column, table_item)

        self.style_table_widget.cellClicked.connect(self._on_table_item_clicked)

        self.video_widget = QVideoWidget()
        self.player_layout.addWidget(self.video_widget)
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(0, 0, 0, 0)
        self.play_button = QPushButton()
        self.play_button.setEnabled(False)
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_button.clicked.connect(self.play)
        control_layout.addWidget(self.play_button)
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderMoved.connect(self.set_position)
        control_layout.addWidget(self.position_slider)
        self.player_layout.addLayout(control_layout)

        self.back_btn.clicked.connect(self._on_back_to_style_view)
        self.delete_btn.clicked.connect(self._on_delete_item)

        self.playlist.itemClicked.connect(self._on_playlist_item_clicked)
        self.playlist.itemDoubleClicked.connect(self._on_playlist_item_double_clicked)

        self.playlist_widget.setVisible(False)

        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.notify_interval = 100
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.setNotifyInterval(self.notify_interval)
        self.media_player.stateChanged.connect(self.media_state_changed)
        self.media_player.positionChanged.connect(self.play_time_changed)
        self.media_player.durationChanged.connect(self.duration_changed)
        self.media_player.error.connect(self.handle_error)

        self.styles_widget.signal_style_clicked.connect(self.on_style_selected)

        self.detected_result_str = ''
        with open('music_model.pkl', 'rb') as fp:
            self.model = pickle.load(fp)

    def closeEvent(self, event):
        self.media_player.pause()
        self.wave_widget.stop_audio()

    def _change_to_playlist_view(self, style_index):
        self.styles_widget.setVisible(False)
        self.playlist_widget.setVisible(True)
        self.selected_style_index = style_index
        self._refresh_playlist()

    def _refresh_playlist(self):
        files = self.songs_data.get(globals.styles[self.selected_style_index], [])
        self.playlist_items = []
        self.playlist.clear()
        flip_count = False
        for file in files:
            flip_count = False if flip_count else True
            list_item = QListWidgetItem(os.path.basename(file))
            setattr(list_item, 'full_file_name', file)
            list_item.setBackground(Qt.lightGray if flip_count else Qt.white)
            self.playlist_items.append(list_item)
            self.playlist.addItem(list_item)

    def _on_back_to_style_view(self):
        self.styles_widget.setVisible(True)
        self.playlist_widget.setVisible(False)
        self.selected_song_name = ''
        self.delete_btn.setEnabled(False)

    def _get_cur_style_dir(self):
        return os.path.join(self.location_root, 'playlists', globals.styles[self.selected_style_index])

    @staticmethod
    def _pop_message_box(alert_text):
        result_window = MyPopup(has_close=True)
        result_window.label.setText(alert_text)
        result_window.exec()

    def on_style_selected(self, style_selected):
        self._change_to_playlist_view(globals.styles.index(style_selected))

    def _print_media_state(self):
        if self.media_player.state() == QMediaPlayer.PlayingState:
            print('playing state')
        elif self.media_player.state() == QMediaPlayer.PausedState:
            print('paused state')
        elif self.media_player.state() == QMediaPlayer.StoppedState:
            print('stopped state')

    def _on_table_item_clicked(self, row, col):
        style_index = row * self.column_num + col
        if style_index >= globals.style_num:
            return
        self._change_to_playlist_view(style_index)

    def _on_playlist_item_clicked(self, item):
        self.selected_song_name = getattr(item, 'full_file_name')
        self.delete_btn.setEnabled(True)

    def _on_playlist_item_double_clicked(self, item):
        if self.selected_style_index == -1:
            return
        filename = getattr(item, 'full_file_name')
        if os.path.isfile(filename):
            self.current_song_label.setText(os.path.basename(filename))
            self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(filename)))
            self.wave_widget.load_file(filename)
            self.play()
        else:
            self._pop_message_box('找不到文件:%s' % filename)

    def _on_delete_item(self):
        if not self.selected_song_name:
            return
        if self.selected_style_index == -1:
            return
        self.songs_data[globals.styles[self.selected_style_index]].pop(self.selected_song_name, None)
        self.songs_data_manager.write_songs_data(self.songs_data)
        self._refresh_playlist()

    def _import_files(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        names = file_dialog.getOpenFileNames(None, 'open wav file', '.', 'AUDIO(*.wav *.mp3)')
        if not names[0]:
            return
        if not isinstance(names[0], list):
            audio_names = [names[0]]
        else:
            audio_names = names[0]
        self.processing_files_thread = ProcessingFilesThread(main_widget=self, names=audio_names)
        self.processing_files_thread.start()
        main_window_geometry = self.geometry()
        self.progress_window = MyPopup(main_widget=self)
        self.progress_window.exec()
        self.processing_files_thread.wait()
        self._pop_message_box(self.detected_result_str)
        self._refresh_playlist()

    def play(self):
        self.play_button.setEnabled(True)
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
            self.wave_widget.pause_audio()
        else:
            self.media_player.play()
            self.wave_widget.start_audio()

    def media_state_changed(self, state):
        if state == QMediaPlayer.PlayingState:
            self.play_button.setIcon(
                    self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.play_button.setIcon(
                    self.style().standardIcon(QStyle.SP_MediaPlay))

        if state == QMediaPlayer.StoppedState:
            self.wave_widget.stop_audio()

    def play_time_changed(self, play_time):
        self.wave_widget.set_cur_play_time(play_time)
        self.position_slider.setValue(play_time)

    def duration_changed(self, duration):
        self.position_slider.setRange(0, duration)

    def set_position(self, position):
        self.media_player.setPosition(position)

    def handle_error(self):
        self.play_button.setEnabled(False)

    def _generate_colors(self, num):
        colors = []
        for r_value in range(0, 256, 20):
            for g_value in range(0, 256, 20):
                for b_value in range(0, 256, 20):
                    colors.append((r_value, g_value, b_value))

        colors_choosen = random.sample(colors, num)
        self.qcolors = []
        for color in colors_choosen:
            self.qcolors.append(QColor(color[0], color[1], color[2], 127))


if __name__ == '__main__':
    if os.path.exists('converted'):
        shutil.rmtree('converted')
    os.mkdir('converted')
    app = QApplication(sys.argv)
    app_icon = QIcon()
    app_icon.addFile('res/main_window_icon.jpg', QSize(16, 16))
    app.setWindowIcon(app_icon)
    myWin = MyMainForm()
    myWin.show()
    sys.exit(app.exec_())
