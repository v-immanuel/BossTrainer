# BossTrainer
A high-precision reaction trainer for mastering boss attack patterns through frame-perfect video synchronization. Practice deflect timings with real-time feedback using 60 FPS footage.

Unlike traditional reaction tests, this trainer uses real gameplay footage to build muscle memory for specific combat animations, providing a low-overhead way to practice frame-perfect parries outside of the game environment.

## How it Works

The BossTrainer follows a "Capture, Analyze, Practice" workflow to ensure maximum accuracy:

- **Capture:** Record a "perfect" deflect/parry in-game using **OBS Studio**. 

   * *Tip:* Enable an Input Overlay in OBS so your keypresses (e.g., `E`) are visible on the recording.
   
- **Analyze:** Open the recording in a frame-accurate player like **mpv**. Scrub through the video to find the exact timestamp/frame where the input occurs.

- **Configure:** Add these timestamps to your timing list. 

- **Train:** The BossTrainer plays the video. You must press the key at the exact moment.

   * A **Beep Sound** triggers at the target timestamp to reinforce auditory muscle memory.
   
   * High-accuracy feedback is provided in milliseconds (ms).

## Controls & Hotkeys

The trainer is designed to build universal muscle memory. Even if you play on a different platform (Console, Mobile, Tablet) or use different keybindings, training the visual-to-motor response remains highly effective.

| Action | Hotkey | Description |
| :--- | :--- | :--- |
| **Deflect** | `E` | Your primary parry/deflect action. Timing is measured against this input. |
| **Start / Pause** | `S` | Starts or pauses the current training session. |
| **Reset** | `R` | Resets the video and timer to the beginning. |


> **Pro-Tip:** The goal is to synchronize your brain's reaction to the boss's animation. Once your "visual trigger" is calibrated, the skill transfers seamlessly to other controllers or touchscreens.


## Feedback System

The trainer calculates the delta between your input and the target frame:

| Timing | Result | Description |
| :--- | :--- | :--- |
| **< 150 ms** | **EARLY** | You pressed the button before the target. |
| **± 49 ms** | **PERFECT** | Frame-perfect execution. |
| **± 99 ms** | **GOOD** | Solid timing, consistent with high-level play. |
| **± 149  ms** | **OK** | Barely made the window. |
| **> 150 ms** | **LATE** | Too slow for this boss mechanic. |
| **No Input** | **MISS** | You missed the window entirely. |

## System Requirements & Performance

While the trainer was developed on high-end hardware to ensure frame-perfect synchronization, it is designed to be efficient.

**Running the Trainer:** 

Can be executed on most modern laptops and PCs. As long as your CPU is not throttled (100% usage) and the video plays smoothly without stuttering, the timing measurements will remain accurate.

**Creating Content:** 

Recording 60 FPS gameplay with high bitrate via OBS Studio requires more powerful hardware to avoid "skipped frames," which would ruin the timing data.

### Development Environment (Reference)
* **OS:** Linux
* **Hardware:** Intel Core Ultra 9 285HX (24 Cores) | NVIDIA RTX 5070 (16 GB VRAM)
* **Performance:** Tested for ultra-low input latency and stable 60 FPS video synchronization.

## Sample Data
In the `data/` directory, you will find `void-k-timing.txt`. This file contains the frame-perfect timing data for a specific boss encounter in *Where Winds Meet*.

To use this sample, you need the corresponding video file:

**Download Video:** [https://drive.google.com/file/d/1e5vho6M1c1YDHAoQSPpLFllCfL86wLDx/ (600 MB)]

**Filename:** `void-k.mkv`

**Training:** load the video and load timing via the GUI.

## Installation & Setup

Install Miniconda  [https://docs.anaconda.com/miniconda/] or Anaconda [https://www.anaconda.com/download/]

Clone or download the repository, then navigate into the project folder:

```bash
git clone https://github.com/v-immanuel/BossTrainer.git
cd BossTrainer
```
**(Windows users: Please use the Anaconda Prompt)**

```bash
conda env create -f environment.yml
```

**Run the program**

```bash
conda activate bosstrainer
cd src
python main.py
```


## OBS Recording with the Included Overlay

For accurate timing analysis, your video needs a visible input overlay. I have included my personal presets in the repository.

1. **Install Plugin:** Download and install the [OBS Input Overlay Plugin](https://github.com/universal-input-overlay/input-overlay).
2. **Add WASD Overlay:**
   * In OBS, add an **Input Overlay** source.
   * **Config Path:** `assets/obs_overlay/wasd-my/wasd.json`
   * **Image Path:** `assets/obs_overlay/wasd-my/wasd.png`
3. **Add Mouse Overlay:**
   * Add another source.
   * **Config Path:** `assets/obs_overlay/mouse/mouse-no-movement.json`
   * **Image Path:** `assets/obs_overlay/mouse/mouse.png`
