import sys
import pygame
import numpy as np
import time
from PyQt6.QtWidgets import (QDialog, QApplication, QWidget, QLabel, QVBoxLayout, 
                             QPushButton, QFileDialog, QHBoxLayout, QTextEdit,
                             QSlider, QStyle, QSizePolicy, QCheckBox)
from PyQt6.QtCore import QTimer, Qt, QUrl, QThread
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtWidgets import QMessageBox

from PyQt6.QtGui import QFont

from worker import TrainingWorker

class StatsDialog(QDialog):
    def __init__(self, report_text, stats, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Boss Training Report")
        self.resize(600, 700) 
        
        layout = QVBoxLayout()
        
        # Header
        total = sum(stats.values())
        successes = stats["Perfect"] + stats["Good"] + stats["ok"]
        acc = (successes / total * 100) if total > 0 else 0
        
        header = QLabel(f"Training Accuracy: {acc:.2f}%")
        header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(header)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        # Monospaced Font for clear visibility
        self.text_edit.setFont(QFont("Courier New", 11))
        self.text_edit.setPlainText(report_text)
        layout.addWidget(self.text_edit)

        btn = QPushButton("Close")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)
        self.setLayout(layout)
        
class DeflectionTrainer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Boss Trainer v.0.1 - Beta")
        self.setGeometry(50, 50, 1930, 1098)
        #self.history = []  # list of integers (ms)
        self.timings = []
        self.current_idx = 0
        self.is_training = False
        self.hits = self.early = self.late = self.missed = 0
        self.video_loaded = False
        self.data_loaded = False
        
        self.current_idx = 0
        self._last_queued_idx = -1

        pygame.mixer.init()
        self.beep = pygame.mixer.Sound(buffer=self.create_beep())

        # Thread Setup
        self.worker_thread = QThread()
        self.worker = TrainingWorker()
        self.worker.moveToThread(self.worker_thread)
        self.worker.result_ready.connect(self.on_result)
        self.worker.miss_triggered.connect(self.on_miss)
        self.worker_thread.start()

        self.init_ui()

    def create_beep(self):
        t = np.linspace(0, 0.1, int(44100 * 0.1), False)
        wave = (np.sin(2 * np.pi * 660 * t) * 32767).astype(np.int16)
        return wave.tobytes()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Video
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumHeight(500)
        self.video_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)

        # Feedback Overlay
        self.feedback_label = QLabel("Ready")
        self.feedback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.feedback_label.setStyleSheet("font-size: 100px; font-weight: bold; color: gray;")

        # Stats Label
        self.stats_display = QLabel("exact hits: 0 | early: 0 | too late: 0")
        self.stats_display.setStyleSheet("font-size: 20px; color: white; background: #333; padding: 1 px;")

        # Control Buttons
        btn_layout = QHBoxLayout()
        self.btn_load_vid = QPushButton("1. Load Video")
        self.btn_load_time = QPushButton("2. Load Timings")
        self.btn_start = QPushButton("Start (S)")
        self.btn_reset = QPushButton("Reset (R)")
        self.sound_check = QCheckBox("Deflection Sound")
        self.btn_start.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold;")
        self.btn_start.setEnabled(False)
        self.btn_reset.setEnabled(False)
        self.sound_check.setChecked(True)
        
        # Connects
        self.btn_load_vid.clicked.connect(self.load_video)
        self.btn_load_time.clicked.connect(self.load_timings)
        self.btn_start.clicked.connect(self.toggle_training)
        self.btn_reset.clicked.connect(self.reset_all)

        btn_layout.addWidget(self.btn_load_vid)
        btn_layout.addWidget(self.btn_load_time)
        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_reset)
        btn_layout.addWidget(self.sound_check)
   
        layout.addWidget(self.video_widget)
        layout.addWidget(self.feedback_label)
        layout.addWidget(self.stats_display)
        layout.addLayout(btn_layout)        
        self.setLayout(layout)

        # --- MEDIA CONTROLS ---
        controls_layout = QHBoxLayout()
        
        # Play/Pause Button with system icons
        self.play_button = QPushButton()
        self.play_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.play_button.clicked.connect(self.play_pause_video)
        self.play_button.setEnabled(False)
        
        # Slider
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderMoved.connect(self.set_position) # Wenn man ihn zieht
        self.position_slider.setEnabled(False)
        
        # time label
        self.time_label = QLabel("00:00 / 00:00")
        
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.position_slider)
        controls_layout.addWidget(self.time_label)
        
        layout.addLayout(controls_layout)
        
        # media player slider signals
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)

        self.logic_timer = QTimer()
        self.logic_timer.timeout.connect(self.update_logic)
        self.logic_timer.start(5)

    def toggle_buttons(self):
        # en = 1 ^ self.is_training
        # self.position_slider.setEnabled(self.is_training ^ 1)

        if self.video_loaded is True and self.data_loaded is True:
            self.btn_start.setEnabled(True)
            self.btn_reset.setEnabled(True)

            if self.is_training == True:
                self.position_slider.setEnabled(False)
                self.play_button.setEnabled(False)
            else:
                self.position_slider.setEnabled(True)
                self.play_button.setEnabled(True)
        else:
            self.btn_start.setEnabled(False)
            self.btn_reset.setEnabled(False)
            self.position_slider.setEnabled(False)
            self.play_button.setEnabled(False)
            
    def load_video(self):
        path, _ = QFileDialog.getOpenFileName(self, "Video")
        if path:
            self.media_player.setSource(QUrl.fromLocalFile(path))
            self.feedback_label.setText("video loaded")
            self.video_loaded = True
            self.toggle_buttons()

    def load_timings(self):
        path, _ = QFileDialog.getOpenFileName(self, "Timings")
        if path:
            with open(path, 'r') as f:
                self.timings = sorted([float(l.strip()) for l in f if l.strip()])
            self.reset_all()
            self.data_loaded = True
            self.feedback_label.setText("timings loaded")
            self.toggle_buttons()

    def update_logic(self):
        curr_time = self.media_player.position() / 1000.0
        
        if self.is_training and self.current_idx < len(self.timings):
            # curr_time = self.media_player.position() / 1000.0
            target = self.timings[self.current_idx]
            
            # EARLY Detection
            if curr_time >= (target - 0.500) and self._last_queued_idx != self.current_idx:
                self.worker.prepare_target(target)
                self._last_queued_idx = self.current_idx

            # Beep Sound
            if curr_time >= target:
                if self.sound_check.isChecked(): 
                    self.beep.play()
                
                self.worker.start_cue_timeout(target)
                self.current_idx += 1

        elif self.is_training is True:
        # Check: close to ending of the video?
                if self.current_idx >= len(self.timings):
                    last_target = self.timings[-1]
                    if curr_time >= (last_target + 0.500):
                        #self.print_final_report()
                        self.finalized_training_report()
                        self.is_training = False # Training beenden

    def print_final_report(self):
        print("\n" + "="*30)
        print("--- TRAINER REPORT ---")
        print("="*30)
        
        # 1. clear query
        while not self.worker.log_queue.empty():
            print(self.worker.log_queue.get())
            
        print("-" * 30)
        # 2. output statistics
        print("STATISTICS:")
        for key, value in self.worker.stats.items():
            print(f"  {key}: {value}")
        print("="*30 + "\n")

    def finalized_training_report(self):
        # 1. gather data from queue
        report_lines = []
        while not self.worker.log_queue.empty():
            report_lines.append(self.worker.log_queue.get())
    
        report_text = "\n".join(report_lines)
    
        # 2. std output
        print(report_text)
    
        s = self.worker.stats
        summary = f"Perfect: {s['Perfect']} | Good: {s['Good']} | OK: {s['ok']}\n"
        summary += f"EARLY: {s['EARLY']} | LATE: {s['LATE']} | MISS: {s['MISS']}\n"
        summary += "-" * 40 + "\n"
    
        full_text = summary + "\n".join(report_lines)
        dialog = StatsDialog(full_text, self.worker.stats, self)
        dialog.exec()
    

    def show_summary_popup(self, report_text, stats):
        msg = QMessageBox(self)
        msg.setWindowTitle("Training Session Complete")
    
        # Session Accuracy
        total = sum(stats.values())
        successes = stats["Perfect"] + stats["Good"] + stats["ok"]
        accuracy = (successes / total * 100) if total > 0 else 0
    
        msg.setText(f"### Session Accuracy: {accuracy:.2f}%")
    
        msg.setInformativeText("Check the details below for each timing:")
        msg.setDetailedText(report_text)
    
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
                
    def update_stats(self):
        self.stats_display.setText(
            f"HITS: {self.hits} | EARLY: {self.early} | "
            f"LATE: {self.late} | MISS: {self.missed}"
        )

    def reset_all(self):
        self.is_training = False
        self.media_player.stop()
        self.media_player.setPosition(0)
        self.current_idx = 0
        self._last_queued_idx = -1 # Auch hier zurücksetzen
        self.hits = self.early = self.late = self.missed = 0
        
        # reset stats
        self.worker.stats = {"Perfect": 0, "Good": 0, "ok": 0, "EARLY": 0, "LATE": 0, "MISS": 0}
    
        # clear queue
        while not self.worker.log_queue.empty():
            self.worker.log_queue.get()
        
        self.update_stats()
        self.feedback_label.setText("Ready")
        QTimer.singleShot(500, self.clear_feedback)
         
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_E and self.is_training:
            # record time and pass it to worker process
            p_time = self.media_player.position() / 1000.0
            self.worker.handle_keypress(p_time)
        elif event.key() == Qt.Key.Key_S: self.toggle_training()
        elif event.key() == Qt.Key.Key_R: self.reset_all()

    def on_result(self, res, color, ms):
        #if res == "HIT":
        #  self.hits += 1
        if color == "green":
            self.hits += 1
        elif res == "EARLY":
            self.early += 1
        else:
            self.late += 1
        self.show_feedback(f"{res} ({ms}ms)", color)

    def on_miss(self):
        self.missed += 1
        self.show_feedback("MISS!", "red")

    def show_feedback(self, txt, col):
        self.feedback_label.setText(txt)
        self.feedback_label.setStyleSheet(f"color: {col}; font-size: 80px; font-weight: bold;")
        self.stats_display.setText(f"HITS: {self.hits} | EARLY: {self.early} | LATE: {self.late} | MISS: {self.missed}")
        # QTimer.singleShot(400, self.clear_feedback)

    def clear_feedback(self):
        #if "yellow" in self.feedback_label.styleSheet() or self.feedback_label.text() == "E":
        self.feedback_label.setText("")


    def toggle_training(self):
        if not self.is_training:
            self.is_training = True
            self.btn_start.setText("Stop (S)")
            self.btn_start.setStyleSheet("background-color: #c62828; color: white;")
            self.media_player.play()
            self.feedback_label.setText("")
        else:
            self.is_training = False
            self.btn_start.setText("Start (S)")
            self.btn_start.setStyleSheet("background-color: #2e7d32; color: white;")
            self.media_player.pause()

        self.toggle_buttons()
        
    def toggle_training(self):
        self.is_training = not self.is_training
        if self.is_training: self.media_player.play()
        else: self.media_player.pause()

    # --- media player control  ---
    def play_pause_video(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            self.play_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        else:
            self.media_player.play()
            self.play_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))

    def position_changed(self, position):
        # updates the slide while the video is played
        self.position_slider.setValue(position)
        self.update_duration_label(position, self.media_player.duration())

    def duration_changed(self, duration):
        # update duration
        self.position_slider.setRange(0, duration)
        self.update_duration_label(self.media_player.position(), duration)

    def set_position(self, position):
        # move to specific position according to the slider
        self.media_player.setPosition(position)

    def update_duration_label(self, current, total):
        curr = time.strftime('%M:%S', time.gmtime(current / 1000))
        tot = time.strftime('%M:%S', time.gmtime(total / 1000))
        self.time_label.setText(f"{curr} / {tot}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = DeflectionTrainer()
    ex.show()
    sys.exit(app.exec())
