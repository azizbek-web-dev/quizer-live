# -*- coding: utf-8 -*-
"""Quizer jonli efir: statistika ekrani -> RTMP (Telegram live).
Bloklar: katta raqamlar (2), universitetlar faolligi (3), hozir onlayn (4),
burchakda muallif imzosi va hazilomuz El Klasiko kartasi.
"""
import json, math, os, subprocess, sys, threading, time
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 12
BASE = os.path.dirname(os.path.abspath(__file__))
SSH = ["ssh", "-i", os.environ.get("SSH_KEY_PATH", "key.pem"),
       "-o", "ConnectTimeout=12", "-o", "StrictHostKeyChecking=no",
       "-o", "BatchMode=yes", "-p", "22", os.environ.get("SSH_TARGET", ""),
       "timeout 40 php8.4 /home/g/grizzly26/qstats.php 2>/dev/null"]

FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def F(bold, size):
    return ImageFont.truetype(FB if bold else FR, size)

BG = (9, 20, 34)
CARD = (16, 36, 56)
CARD2 = (13, 30, 47)
CYAN = (45, 212, 191)
BLUE = (56, 150, 248)
WHITE = (240, 248, 252)
GRAY = (148, 178, 198)
GREEN = (52, 211, 153)
RED = (248, 113, 113)
GOLD = (250, 204, 21)

stats = {}
stats_lock = threading.Lock()
stop = False

def fetch_loop():
    while not stop:
        try:
            r = subprocess.run(SSH, capture_output=True, text=True, timeout=60)
            line = (r.stdout or "").strip().splitlines()
            if line:
                data = json.loads(line[-1])
                with stats_lock:
                    stats.clear(); stats.update(data)
        except Exception as e:
            print("fetch xato:", e, flush=True)
        for _ in range(20):
            if stop: return
            time.sleep(1)

def fmt(n):
    return f"{int(round(n)):,}".replace(",", " ")

def card(d, box, fill=CARD, r=28):
    d.rounded_rectangle(box, radius=r, fill=fill)

def txt(d, x, y, s, f, fill, anchor="la"):
    d.text((x, y), s, font=f, fill=fill, anchor=anchor)

def fit(s, f, maxw):
    while s and f.getlength(s) > maxw:
        s = s[:-1]
    return s

disp = {}  # animatsiyalanadigan sonlar
def anim(key, target, speed=0.12):
    cur = disp.get(key, float(target))
    cur += (float(target) - cur) * speed
    if abs(float(target) - cur) < 0.6:
        cur = float(target)
    disp[key] = cur
    return cur

barsa = Image.open(f"{BASE}/assets/barsa.png").convert("RGBA")
real = Image.open(f"{BASE}/assets/real.png").convert("RGBA")

def render(t):
    with stats_lock:
        s = dict(stats)
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img, "RGBA")
    # fon bezaklari
    for (cx, cy, r, col) in [(980, 120, 300, (45, 212, 191, 16)), (60, 1750, 340, (56, 150, 248, 14))]:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)

    # --- Sarlavha ---
    txt(d, 56, 46, "QUIZER", F(True, 66), CYAN)
    txt(d, 56, 122, "JONLI STATISTIKA EFIRI", F(True, 30), GRAY)
    pulse = 0.55 + 0.45 * math.sin(t * 3.2)
    d.ellipse([856, 62, 890, 96], fill=(239, 68, 68, int(140 + 115 * pulse)))
    txt(d, 900, 58, "LIVE", F(True, 40), WHITE)
    clock = s.get("time_tashkent", "--:--")
    txt(d, 1024, 118, clock, F(True, 40), WHITE, anchor="ra")
    txt(d, 1024, 164, s.get("date_tashkent", ""), F(False, 26), GRAY, anchor="ra")

    if not s:
        txt(d, W // 2, 900, "Ma'lumot yuklanmoqda...", F(True, 44), GRAY, anchor="ma")
        return img

    tot, tod = s["totals"], s["today"]

    # --- (4) Hozir onlayn ---
    card(d, [48, 210, 1032, 372])
    on5 = anim("on5", s.get("online5", 0), 0.2)
    gp = 0.5 + 0.5 * math.sin(t * 2.6)
    d.ellipse([92, 262, 138, 308], fill=(52, 211, 153, int(120 + 135 * gp)))
    txt(d, 162, 240, "HOZIR ONLAYN", F(True, 34), GRAY)
    txt(d, 162, 282, fmt(on5), F(True, 62), GREEN)
    txt(d, 1000, 258, "oxirgi 30 daqiqada faol:", F(False, 28), GRAY, anchor="ra")
    txt(d, 1000, 296, fmt(anim("on30", s.get("online30", 0), 0.2)), F(True, 44), WHITE, anchor="ra")
    if s.get("online5", 0) == 0 and s.get("online30", 0) == 0:
        txt(d, W // 2, 388, "Tungi rejim — shahar uxlayapti, ertalab jonlanamiz", F(False, 28), GOLD, anchor="ma")

    # --- (2) Katta raqamlar ---
    cells = [("FOYDALANUVCHILAR", "users", CYAN), ("TESTLAR", "tests", BLUE),
             ("URINISHLAR", "attempts", GOLD), ("SAVOLLAR", "questions", GREEN)]
    cw, ch, gap, x0, y0 = 476, 196, 32, 48, 440
    for i, (label, key, col) in enumerate(cells):
        x = x0 + (i % 2) * (cw + gap)
        y = y0 + (i // 2) * (ch + gap)
        card(d, [x, y, x + cw, y + ch], CARD2)
        d.rectangle([x, y + 18, x + 8, y + ch - 18], fill=col)
        txt(d, x + 34, y + 26, label, F(True, 30), GRAY)
        txt(d, x + 34, y + 72, fmt(anim(key, tot[key])), F(True, 74), WHITE)

    # --- Bugun lentasi ---
    by = 896
    card(d, [48, by, 1032, by + 84], (20, 46, 40))
    line = (f"BUGUN:  +{tod['users']} yangi   •   {tod['tests']} test   •   "
            f"{tod['attempts']} urinish   •   {tod['uploads_done']} tayyor")
    f = F(True, 30)
    txt(d, W // 2, by + 24, fit(line, f, 940), f, GREEN, anchor="ma")

    # --- (3) Universitetlar faolligi ---
    uy = 1030
    scope = "bugun" if s.get("top_scope") == "today" else "jami"
    txt(d, 56, uy, "UNIVERSITETLAR FAOLLIGI", F(True, 36), WHITE)
    txt(d, 1024, uy + 6, f"({scope})", F(False, 28), GRAY, anchor="ra")
    tops = s.get("top_universities", [])[:5]
    total_att = max(tot["attempts"], 1)
    shown = sum(x["c"] for x in tops)
    rows = [(x["name"], x["c"]) for x in tops]
    rest = total_att - shown
    if rest > 0 and len(rows) >= 1:
        rows.append(("Boshqalar", rest))
    maxc = max([c for _, c in rows], default=1)
    ry = uy + 62
    for name, c in rows[:5]:
        txt(d, 56, ry, fit(name, F(False, 30), 700), F(False, 30), WHITE)
        txt(d, 1024, ry, fmt(c), F(True, 32), CYAN, anchor="ra")
        bw = int(968 * (c / maxc) * (0.25 + 0.75 * min(1.0, (t % 100) / 1.5)))
        d.rounded_rectangle([56, ry + 44, 56 + max(bw, 26), ry + 62], radius=9, fill=(45, 212, 191, 190))
        ry += 84
    if not rows:
        txt(d, 56, ry, "Hozircha ma'lumot yo'q", F(False, 32), GRAY)

    # --- Oxirgi testlar ---
    ty = 1480
    txt(d, 56, ty, "OXIRGI TESTLAR", F(True, 32), WHITE)
    for j, tt in enumerate(s.get("recent_tests", [])[:3]):
        txt(d, 56, ty + 52 + j * 46, "•  " + fit(tt["title"], F(False, 31), 940), F(False, 31), GRAY)

    # --- El Klasiko (hazilomuz burchak) ---
    ey = 1652
    card(d, [48, ey, 1032, ey + 126], (24, 32, 58))
    b = barsa.resize((88, 88), Image.LANCZOS); r_ = real.resize((88, 88), Image.LANCZOS)
    img.paste(b, (76, ey + 19), b); img.paste(r_, (916, ey + 19), r_)
    txt(d, W // 2, ey + 10, "EL KLASIKO", F(True, 26), GOLD, anchor="ma")
    txt(d, W // 2, ey + 42, "1 — 2", F(True, 52), WHITE, anchor="ma")
    txt(d, W // 2, ey + 102, "Mbappé 41', 88'  •  Raphinha 61'", F(False, 22), GRAY, anchor="ma")

    # --- Muallif imzosi (burchak) ---
    txt(d, 1024, 1846, "Hakimov Azizbek", F(True, 29), WHITE, anchor="ra")
    txt(d, 1024, 1882, "Full Stack dasturchi va tibbiyot talabasi", F(False, 23), GRAY, anchor="ra")
    txt(d, 56, 1862, "devmed.uz/quizer", F(False, 24), (90, 120, 140), anchor="la")
    return img

def main():
    push = os.environ["RTMP_PUSH"]
    th = threading.Thread(target=fetch_loop, daemon=True); th.start()
    print("Birinchi statistika kutilmoqda...", flush=True)
    for _ in range(30):
        with stats_lock:
            if stats: break
        time.sleep(1)
    cmd = ["ffmpeg", "-y", "-v", "info",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast",
           "-b:v", "1700k", "-maxrate", "1900k", "-bufsize", "3400k", "-g", str(FPS * 2),
           "-f", "flv"]
    cmd += [push]
    attempt = 0
    while attempt < 200:
        attempt += 1
        err = open("ffmpeg.log", "ab")
        ff = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=err)
        print(f"EFIR BOSHLANDI (urinish {attempt})", flush=True)
        t0 = time.time()
        frames = 0
        try:
            while True:
                t = time.time() - t0
                frame = render(t)
                ff.stdin.write(frame.tobytes())
                frames += 1
                if frames % 240 == 0:
                    print(f" oqim: {frames} kadr, {t:.0f}s", flush=True)
                dt = time.time() - t0 - t
                sleep = (1 / FPS) - dt
                if sleep > 0: time.sleep(sleep)
                if ff.poll() is not None:
                    break
        except BrokenPipeError:
            print("BrokenPipe: ffmpeg yopildi", flush=True)
        except KeyboardInterrupt:
            break
        try: ff.stdin.close()
        except Exception: pass
        try: ff.wait(timeout=5)
        except Exception: ff.kill()
        err.close()
        try:
            tail = open("ffmpeg.log", "rb").read()[-1500:].decode("utf-8", "replace")
            print("ffmpeg log (oxiri):\n", tail, flush=True)
        except Exception:
            pass
        print("5s dan keyin qayta ulanish...", flush=True)
        time.sleep(5)
    globals()["stop"] = True

if __name__ == "__main__":
    main()
