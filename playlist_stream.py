# -*- coding: utf-8 -*-
"""YouTube playlist loop efir (GitHub Actions).

Foydalanuvchi bergan 8 ta YouTube videoni ketma-ket yuklab, bir xil
formatga (1280x720, 30fps, AAC) keltirib, cheksiz halqada Telegram
RTMP efiriga uzatadi. Tartib — foydalanuvchi yuborgan tartib.
Bir halqa davomiyligi: ~31 daqiqa 48 soniya.
"""
import glob, os, subprocess, sys, time

PLAYLIST = [
    "https://www.youtube.com/watch?v=DQIhJ_LBtOQ",  # TOXI$ — November (181s)
    "https://www.youtube.com/watch?v=Ic5sSlqO-c8",  # Billie Eilish — WILDFLOWER lyrics (260s)
    "https://www.youtube.com/watch?v=fukGbiPuBjU",  # Arctic Monkeys — I Wanna Be Yours (184s)
    "https://www.youtube.com/watch?v=VmXJPp22j5o",  # Jah Khalib — Колыбельная (173s)
    "https://www.youtube.com/watch?v=Q2AXnU8pS70",  # А если это любовь slowed (332s)
    "https://www.youtube.com/watch?v=PvKw4ljBohA",  # Britney Spears — Criminal lyrics (224s)
    "https://www.youtube.com/watch?v=ud49OArJsys",  # Ja tebia liubliu (330s)
    "https://www.youtube.com/watch?v=uJ2raEnG6GQ",  # Shohruhxon — Qo'g'irchoq (224s)
]

RTMP = os.environ.get("RTMP_PUSH", "")
WORK = "/tmp/playlist_work"
os.makedirs(WORK, exist_ok=True)


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def run(cmd):
    log("RUN:", " ".join(cmd)[:200])
    return subprocess.run(cmd).returncode


def download(i, url):
    out = os.path.join(WORK, f"raw{i}.%(ext)s")
    for attempt in (1, 2, 3):
        rc = run([
            "yt-dlp", "--no-warnings", "--no-playlist", "--retries", "3",
            "--extractor-args", "youtube:player_client=android",
            "-f", "bv*[height<=720]+ba/b[height<=720]/b",
            "--merge-output-format", "mp4",
            "-o", out, url,
        ])
        files = sorted(glob.glob(os.path.join(WORK, f"raw{i}.*")))
        files = [f for f in files if not f.endswith(".part")]
        if rc == 0 and files:
            log(f"yuklandi [{i}]: {files[0]}")
            return files[0]
        log(f"yuklash urinishi {attempt} muvaffaqiyatsiz [{i}] rc={rc}")
        time.sleep(15)
    return None


def normalize(i, raw):
    norm = os.path.join(WORK, f"norm{i}.mp4")
    rc = run([
        "ffmpeg", "-y", "-i", raw,
        "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,"
               "pad=1280:720:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-maxrate", "2800k", "-bufsize", "5600k",
        "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2",
        norm,
    ])
    if rc == 0 and os.path.exists(norm):
        log(f"tayyor [{i}]: {norm}")
        return norm
    log(f"normalize xato [{i}] rc={rc}")
    return None


def main():
    if not RTMP:
        log("RTMP_PUSH topilmadi")
        sys.exit(1)
    norms = []
    for i, url in enumerate(PLAYLIST):
        raw = download(i, url)
        if not raw:
            log(f"O'TKAZIB YUBORILDI [{i}]: {url}")
            continue
        n = normalize(i, raw)
        if n:
            norms.append(n)
        try:
            os.remove(raw)
        except OSError:
            pass
    if not norms:
        log("HECH BIR VIDEO TAYYOR BO'LMADI")
        sys.exit(1)
    log(f"Playlist tayyor: {len(norms)}/{len(PLAYLIST)} video")
    lst = os.path.join(WORK, "list.txt")
    with open(lst, "w") as f:
        for n in norms:
            f.write(f"file '{n}'\n")
    while True:
        log("EFIR BOSHLANDI (loop)")
        rc = run([
            "ffmpeg", "-re", "-stream_loop", "-1",
            "-f", "concat", "-safe", "0", "-i", lst,
            "-c", "copy", "-flush_packets", "1",
            "-f", "flv", RTMP,
        ])
        log(f"ffmpeg tugadi rc={rc}; 10s dan keyin qayta ulanadi")
        time.sleep(10)


if __name__ == "__main__":
    main()
