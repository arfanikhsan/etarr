"""
pose_sanity_check.py

Simplest end-to-end check that OpenCV + MediaPipe work on this machine.

  1. Prints versions and confirms the MediaPipe Tasks API is available
  2. Downloads the Pose Landmarker model once (saved next to this script)
  3. Opens your webcam and draws head + arm landmarks live (mirrored view)
  4. Prints wrist positions twice a second
  5. Prints a PASS / FAIL summary when you quit

Setup:  pip install mediapipe
        (this already installs OpenCV - do not also install opencv-python)
Run:    python pose_sanity_check.py
Quit:   press q in the video window (or Ctrl+C in the terminal)
"""

import sys
import time
import urllib.request
from pathlib import Path

try:
    import cv2
    import mediapipe as mp
    from mediapipe.tasks.python import BaseOptions, vision
except ImportError as e:
    sys.exit(f"[FAIL] Missing package: {e}\nFix: pip install mediapipe   (it installs OpenCV too)")

CAM_INDEX = 0  # change to 1, 2, ... if you have several cameras
MODEL_NAME = "pose_landmarker_lite.task"  # later: try the "full" variant for accuracy
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
    "pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
)
MODEL_PATH = Path(__file__).with_name(MODEL_NAME)

# Pose landmark indices. LEFT / RIGHT = the person's own left / right.
NOSE, L_EAR, R_EAR = 0, 7, 8
L_SHOULDER, R_SHOULDER = 11, 12
L_ELBOW, R_ELBOW = 13, 14
L_WRIST, R_WRIST = 15, 16
L_INDEX, R_INDEX = 19, 20

LEFT_COLOR = (255, 160, 0)  # BGR, blue-ish
RIGHT_COLOR = (0, 160, 255)  # BGR, orange
HEAD_COLOR = (0, 220, 0)
BODY_COLOR = (200, 200, 200)
LEFT_BONES = [(L_SHOULDER, L_ELBOW), (L_ELBOW, L_WRIST), (L_WRIST, L_INDEX)]
RIGHT_BONES = [(R_SHOULDER, R_ELBOW), (R_ELBOW, R_WRIST), (R_WRIST, R_INDEX)]


def fail(msg):
    print(f"\n[FAIL] {msg}")
    sys.exit(1)


def ensure_model():
    if MODEL_PATH.exists() and MODEL_PATH.stat().st_size > 100_000:
        print(f"[ok] model found: {MODEL_PATH.name}")
        return
    print(f"[..] downloading pose model to {MODEL_PATH} ...")
    tmp = MODEL_PATH.with_suffix(".part")
    try:
        urllib.request.urlretrieve(MODEL_URL, tmp)
        tmp.replace(MODEL_PATH)
    except Exception as e:
        tmp.unlink(missing_ok=True)
        fail(
            f"could not download the model ({e}).\n"
            f"       Download it manually from:\n       {MODEL_URL}\n"
            f"       and save it next to this script as {MODEL_NAME}"
        )
    print("[ok] model downloaded")


def open_camera():
    if sys.platform.startswith("win"):
        backends = [cv2.CAP_DSHOW, cv2.CAP_ANY]  # DirectShow first: opens faster on Windows
    else:
        backends = [cv2.CAP_ANY]
    for backend in backends:
        cap = cv2.VideoCapture(CAM_INDEX, backend)
        if cap.isOpened():
            ok, frame = cap.read()
            if ok:
                h, w = frame.shape[:2]
                print(f"[ok] camera {CAM_INDEX} opened ({w}x{h})")
                return cap
        cap.release()
    fail(
        f"could not read from camera {CAM_INDEX}. Close other apps that use the webcam, "
        "check the OS camera-privacy settings, or change CAM_INDEX."
    )


def vis_of(p):
    v = getattr(p, "visibility", None)
    return 1.0 if v is None else float(v)


def is_visible(p, threshold=0.5):
    return vis_of(p) >= threshold


def to_px(p, w, h):
    return int(p.x * w), int(p.y * h)


def draw_upper_body(frame, lms):
    """Draw head points and both arms onto frame (in place)."""
    h, w = frame.shape[:2]
    if is_visible(lms[L_SHOULDER]) and is_visible(lms[R_SHOULDER]):
        cv2.line(frame, to_px(lms[L_SHOULDER], w, h), to_px(lms[R_SHOULDER], w, h), BODY_COLOR, 2)
    for bones, color in ((LEFT_BONES, LEFT_COLOR), (RIGHT_BONES, RIGHT_COLOR)):
        for a, b in bones:
            if is_visible(lms[a]) and is_visible(lms[b]):
                cv2.line(frame, to_px(lms[a], w, h), to_px(lms[b], w, h), color, 3)
        for i in {i for pair in bones for i in pair}:
            if is_visible(lms[i]):
                cv2.circle(frame, to_px(lms[i], w, h), 6, color, -1)
    for i in (NOSE, L_EAR, R_EAR):
        if is_visible(lms[i]):
            cv2.circle(frame, to_px(lms[i], w, h), 6, HEAD_COLOR, -1)


def wrist_line(name, img_lm, world_lm):
    return (
        f"  {name} wrist  image(x,y,z)=({img_lm.x:+.2f}, {img_lm.y:+.2f}, {img_lm.z:+.2f})  "
        f"world_m=({world_lm.x:+.2f}, {world_lm.y:+.2f}, {world_lm.z:+.2f})  seen={vis_of(img_lm):.2f}"
    )


def main():
    print(f"[ok] Python {sys.version.split()[0]} | OpenCV {cv2.__version__} | MediaPipe {mp.__version__}")
    ensure_model()
    cap = open_camera()

    options = vision.PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(MODEL_PATH)),
        running_mode=vision.RunningMode.VIDEO,
        num_poses=1,
    )

    frames = detected = 0
    start = last_print = time.monotonic()
    last_ts = -1
    try:
        with vision.PoseLandmarker.create_from_options(options) as landmarker:
            print("[ok] pose model loaded - move your arms in front of the camera. Press q to quit.\n")
            while True:
                ok, frame = cap.read()
                if not ok:
                    print("[warn] camera returned no frame; stopping")
                    break

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                now = time.monotonic()
                ts = max(int((now - start) * 1000), last_ts + 1)  # timestamps must strictly increase
                last_ts = ts
                result = landmarker.detect_for_video(image, ts)
                frames += 1

                has_pose = bool(result.pose_landmarks)
                if has_pose:
                    detected += 1
                    lms = result.pose_landmarks[0]
                    world = result.pose_world_landmarks[0]
                    draw_upper_body(frame, lms)
                    if now - last_print >= 0.5:
                        last_print = now
                        print(f"[{now - start:6.1f}s]")
                        print(wrist_line("L", lms[L_WRIST], world[L_WRIST]))
                        print(wrist_line("R", lms[R_WRIST], world[R_WRIST]))
                elif now - last_print >= 0.5:
                    last_print = now
                    print(f"[{now - start:6.1f}s] no person detected")

                display = cv2.flip(frame, 1)  # mirror view; text is drawn after so it stays readable
                fps = frames / max(now - start, 1e-6)
                label = "pose OK" if has_pose else "no pose"
                cv2.putText(display, f"{label}   FPS {fps:4.1f}", (10, 28),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                try:
                    cv2.imshow("pose sanity check (q to quit)", display)
                except cv2.error:
                    fail(
                        "OpenCV cannot open windows - probably a headless build is installed.\n"
                        "       Fix: pip uninstall -y opencv-python opencv-python-headless\n"
                        "            pip install --force-reinstall opencv-contrib-python"
                    )
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        cv2.destroyAllWindows()

    elapsed = max(time.monotonic() - start, 1e-6)
    print(f"\nProcessed {frames} frames in {elapsed:.1f}s ({frames / elapsed:.1f} FPS); "
          f"pose found in {detected}.")
    if frames == 0:
        fail("no frames were processed.")
    if detected == 0:
        fail("the pipeline ran but never saw a person. Check lighting and step back so "
             "your head, shoulders and arms are in frame.")
    print("[PASS] OpenCV + MediaPipe pose tracking works on this machine.")


if __name__ == "__main__":
    main()