from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QMutex, QMutexLocker
import queue

class TrainingWorker(QObject):
    result_ready = pyqtSignal(str, str, int)
    miss_triggered = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.mutex = QMutex()
        self.active_target = None
        self.tolerance = 0.150  # 150ms window
        self.tolerance_good = 0.100 # 100 ms
        self.tolerance_perfect = 0.05 # 50 ms
        self.log_queue = queue.Queue() # logging
        self.stats = {"Perfect": 0, "Good": 0, "ok": 0, "EARLY": 0, "LATE": 0, "MISS": 0}

    def prepare_target(self, target_time):
        """Preload to recognize EARLY"""
        with QMutexLocker(self.mutex):
            # only set if not another cue is active
            if self.active_target is None:
                self.active_target = target_time

    def start_cue_timeout(self, target_time):
        """Starts the countdown for MISS."""
        QTimer.singleShot(500, lambda: self.check_miss(target_time))

    def handle_keypress(self, press_time):
        target_from_file = 0
        
        with QMutexLocker(self.mutex):
            if self.active_target is None:
                return
            
            target = self.active_target
            #self.active_target = None
            
            # curtrent timing from file
            target_from_file = self.active_target
            
            diff = press_time - target
            ms = int(diff * 1000)

            # ignore if key was pressed 300 ms before
            if diff < -0.300:
                return # nothing happened
            # ---------------------------------

            # Get result
            absv = abs(diff)
            res = ""
            if absv <= self.tolerance:
                if absv <= self.tolerance_perfect:
                    res = "Perfect"
                    self.result_ready.emit("Perfect", "green", ms)
                elif absv <= self.tolerance_good:
                    res = "Good"
                    self.result_ready.emit("Good", "green", ms)
                else:
                    res = "ok"
                    self.result_ready.emit("ok", "green", ms)
            elif diff < -self.tolerance:
                res = "EARLY"
                self.result_ready.emit("EARLY", "blue", ms)
            else:
                res = "LATE"
                self.result_ready.emit("LATE", "red", ms)
                
            # increase stats
            self.stats[res] += 1
            
            # logging target according to the timing file
            log_entry = f"TIMING: {target:<8} | Result: {res:<8} | Offset: {ms:>+4}ms"
            self.log_queue.put(log_entry)

            # Keypress has been processed, remove target
            self.active_target = None
            

    def check_miss(self, target_time):
        with QMutexLocker(self.mutex):
            if self.active_target == target_time:
                self.active_target = None
                self.stats["MISS"] += 1
                # logg event if not pressed
                self.log_queue.put(f"TIMING: {target_time:<8} | Result: MISS")
                self.miss_triggered.emit()
