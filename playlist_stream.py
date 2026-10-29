# -*- coding: utf-8 -*-
"""YouTube playlist loop efir v2 (GitHub Actions).

Tayyor videolar (960x540, h264+AAC, bir xil format) GitHub Release
(playlist-v1) dan yuklab olinadi va cheksiz halqada Telegram RTMP
efiriga uzatiladi. Tartib — foydalanuvchi yuborgan tartib.
Bir halqa: ~31 daqiqa 48 soniya (8 video).
YouTube dan to'g'ridan yuklash GH serverlarida bloklangani uchun
videolar oldindan tayyorlanib Release ga qo'yilgan.
"""
import os, subprocess, sys, time

BASE_URL = "https://github.com/azizbek-web-dev/quizer-live/releases/download/playlist-v1"
FILES = [f"norm{i}.mp4" for i in range(8)]
RTMP = os.environ.get("RTMP_PUSH", "")
WORK = "/tmp/playlist_work"
os.makedirs(WORK, exist_ok=True)


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def run(cmd):
    log("RUN:", " ".join(cmd)[:160])
    return subprocess.run(cmd).returncode


def main():
    if not RTMP:
        log("RTMP_PUSH topilmadi")
        sys.exit(1)
    paths = []
    for name in FILES:
        dst = os.path.join(WORK, name)
        ok = False
        for attempt in (1, 2, 3):
            rc = run(["curl", "-sL", "--retry", "3", "-o", dst, f"{BASE_URL}/{name}"])
            if rc == 0 and os.path.exists(dst) and os.path.getsize(dst) > 1_000_000:
                ok = True
                break
            log(f"yuklash urinishi {attempt} muvaffaqiyatsiz: {name}")
            time.sleep(10)
        if not ok:
            log("Fayl yuklanmadi, to'xtayman:", name)
            sys.exit(1)
        log("yuklandi:", name, os.path.getsize(dst))
        paths.append(dst)
    lst = os.path.join(WORK, "list.txt")
    with open(lst, "w") as f:
        for p in paths:
            f.write(f"file '{p}'\n")
    log("Playlist tayyor: 8/8 video")
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
