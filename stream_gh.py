# -*- coding: utf-8 -*-
"""Quizer jonli efir (GitHub Actions): B-variant dizayn (binafsha, shisha kartalar).
Statistika Beget dan SSH orqali, oqim RTMP orqali Telegram ga.
"""
import json, math, os, subprocess, threading, time
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1920, 1080, 12
BASE = os.path.dirname(os.path.abspath(__file__))
SSH = ["ssh", "-i", os.environ.get("SSH_KEY_PATH", "key.pem"),
       "-o", "ConnectTimeout=12", "-o", "StrictHostKeyChecking=no",
       "-o", "BatchMode=yes", "-p", "22", os.environ.get("SSH_TARGET", ""),
       "timeout 40 php8.4 /home/g/grizzly26/qstats.php 2>/dev/null"]

FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def F(bold, size):
    return ImageFont.truetype(FB if bold else FR, size)

# --- B-variant palitra ---
TITLE = (255, 255, 255)
LABEL = (216, 205, 245)
SUB = (196, 186, 232)
ACCENT = (192, 132, 252)
ACCENT2 = (244, 114, 182)
GOLD = (250, 204, 21)
GREEN = (52, 211, 153)
RED = (248, 113, 113)

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

def fit(d, s, f, maxw):
    while s and d.textlength(s, font=f) > maxw:
        s = s[:-1]
    return s

disp = {}
def anim(key, target, speed=0.12):
    cur = disp.get(key, float(target))
    cur += (float(target) - cur) * speed
    if abs(float(target) - cur) < 0.6:
        cur = float(target)
    disp[key] = cur
    return cur

barsa = Image.open(f"{BASE}/assets/barsa.png").convert("RGBA")
real = Image.open(f"{BASE}/assets/real.png").convert("RGBA")

def build_plate():
    bg = Image.open(f"{BASE}/assets/bg.webp").convert("RGB").resize((W, H), Image.LANCZOS)
    ov = Image.new("RGB", (W, H), (96, 64, 190))
    bg = Image.blend(bg, ov, 74 / 255).convert("RGBA")

    def glass(box, r=30, fill_a=28):
        x0, y0, x1, y1 = box
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sd = ImageDraw.Draw(sh)
        sd.rounded_rectangle([x0, y0 + 10, x1, y1 + 10], radius=r, fill=(0, 0, 0, 110))
        bg.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)))
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        ld.rounded_rectangle(box, radius=r, fill=(255, 255, 255, fill_a),
                             outline=(255, 255, 255, 90), width=2)
        bg.alpha_composite(layer)

    cells = [(56, 168), (522, 168), (988, 168), (1454, 168)]
    for (x, y) in cells:
        glass([x, y, x + 438, y + 168])
    glass([56, 372, 880, 540])                 # onlayn
    glass([56, 596, 880, 692], fill_a=44)      # bugun
    glass([936, 848, 1864, 976])               # klasiko
    d = ImageDraw.Draw(bg)
    for (x, y), col in zip(cells, [ACCENT, ACCENT2, GOLD, GREEN]):
        d.rounded_rectangle([x, y + 18, x + 9, y + 150], radius=4, fill=col + (255,))
    labels = ["FOYDALANUVCHILAR", "TESTLAR", "URINISHLAR", "SAVOLLAR"]
    for (x, y), lab in zip(cells, labels):
        d.text((x + 32, y + 24), lab, font=F(True, 29), fill=LABEL + (255,))
    d.text((56, 34), "QUIZER", font=F(True, 64), fill=ACCENT + (255,))
    d.text((58, 106), "JONLI STATISTIKA EFIRI", font=F(True, 27), fill=SUB + (255,))
    d.text((1514, 40), "LIVE", font=F(True, 38), fill=TITLE + (255,))
    d.text((162, 404), "HOZIR ONLAYN", font=F(True, 33), fill=LABEL + (255,))
    d.text((848, 420), "oxirgi 30 daqiqada faol:", font=F(False, 27), fill=SUB + (255,), anchor="ra")
    d.text((936, 372), "UNIVERSITETLAR FAOLLIGI", font=F(True, 34), fill=TITLE + (255,))
    d.text((56, 736), "OXIRGI TESTLAR", font=F(True, 31), fill=TITLE + (255,))
    d.text((1400, 860), "EL KLASIKO", font=F(True, 26), fill=GOLD + (255,), anchor="ma")
    d.text((1400, 892), "1 — 2", font=F(True, 50), fill=TITLE + (255,), anchor="ma")
    d.text((1400, 950), "Mbappé 41', 88'  •  Raphinha 61'", font=F(False, 22), fill=SUB + (255,), anchor="ma")
    b = barsa.resize((92, 92), Image.LANCZOS); r_ = real.resize((92, 92), Image.LANCZOS)
    bg.paste(b, (972, 866), b); bg.paste(r_, (1736, 866), r_)
    d.text((1864, 1004), "Hakimov Azizbek", font=F(True, 29), fill=TITLE + (255,), anchor="ra")
    d.text((1864, 1040), "Full Stack dasturchi va tibbiyot talabasi", font=F(False, 23), fill=SUB + (255,), anchor="ra")
    d.text((56, 1022), "devmed.uz/quizer", font=F(False, 24), fill=SUB + (255,))
    return bg

PLATE = build_plate()

def render(t):
    with stats_lock:
        s = dict(stats)
    img = PLATE.copy()
    d = ImageDraw.Draw(img, "RGBA")
    pulse = 0.55 + 0.45 * math.sin(t * 3.2)
    d.ellipse([1470, 44, 1502, 76], fill=(239, 68, 68, int(140 + 115 * pulse)))
    d.text((1864, 40), s.get("time_tashkent", "--:--"), font=F(True, 44), fill=TITLE + (255,), anchor="ra")
    d.text((1864, 92), s.get("date_tashkent", ""), font=F(False, 25), fill=SUB + (255,), anchor="ra")
    if not s:
        d.text((W // 2, 520), "Ma'lumot yuklanmoqda...", font=F(True, 46), fill=SUB + (255,), anchor="ma")
        return img.convert("RGB")
    tot, tod = s["totals"], s["today"]
    for (x, y), key in zip([(56, 168), (522, 168), (988, 168), (1454, 168)],
                           ["users", "tests", "attempts", "questions"]):
        d.text((x + 32, y + 64), fmt(anim(key, tot[key])), font=F(True, 74), fill=TITLE + (255,))
    gp = 0.5 + 0.5 * math.sin(t * 2.6)
    d.ellipse([96, 428, 140, 472], fill=(52, 211, 153, int(120 + 135 * gp)))
    d.text((162, 444), fmt(anim("on5", s.get("online5", 0), 0.2)), font=F(True, 62), fill=GREEN + (255,))
    d.text((848, 456), fmt(anim("on30", s.get("online30", 0), 0.2)), font=F(True, 42), fill=TITLE + (255,), anchor="ra")
    if s.get("online5", 0) == 0 and s.get("online30", 0) == 0:
        d.text((468, 556), "Tungi rejim — shahar uxlayapti, ertalab jonlanamiz", font=F(False, 27), fill=GOLD + (255,), anchor="ma")
    line = (f"BUGUN:  +{tod['users']} yangi   •   {tod['tests']} test   •   "
            f"{tod['attempts']} urinish   •   {tod['uploads_done']} tayyor")
    f = F(True, 31)
    d.text((468, 628), fit(d, line, f, 780), font=f, fill=GREEN + (255,), anchor="ma")
    for j, tt in enumerate(s.get("recent_tests", [])[:4]):
        d.text((56, 786 + j * 48), "•  " + fit(d, tt["title"], F(False, 31), 800), font=F(False, 31), fill=SUB + (255,))
    scope = "bugun" if s.get("top_scope") == "today" else "jami"
    d.text((1864, 376), f"({scope})", font=F(False, 27), fill=SUB + (255,), anchor="ra")
    tops = s.get("top_universities", [])[:5]
    total_att = max(tot["attempts"], 1)
    shown = sum(x["c"] for x in tops)
    rows = [(x["name"], x["c"]) for x in tops]
    rest = total_att - shown
    if rest > 0 and len(rows) >= 1:
        rows.append(("Boshqalar", rest))
    maxc = max([c for _, c in rows], default=1)
    ry = 436
    for name, c in rows[:5]:
        d.text((936, ry), fit(d, name, F(False, 30), 640), font=F(False, 30), fill=TITLE + (255,))
        d.text((1864, ry), fmt(c), font=F(True, 32), fill=ACCENT + (255,), anchor="ra")
        bw = int(928 * (c / maxc) * (0.25 + 0.75 * min(1.0, (t % 100) / 1.5)))
        d.rounded_rectangle([936, ry + 44, 936 + max(bw, 26), ry + 62], radius=9, fill=ACCENT + (200,))
        ry += 86
    if not rows:
        d.text((936, ry), "Hozircha ma'lumot yo'q", font=F(False, 32), fill=SUB + (255,))
    return img.convert("RGB")

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
           "-f", "flv", push]
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
            tail = open("ffmpeg.log", "rb").read()[-1200:].decode("utf-8", "replace")
            print("ffmpeg log (oxiri):\n", tail, flush=True)
        except Exception:
            pass
        print("5s dan keyin qayta ulanish...", flush=True)
        time.sleep(5)
    globals()["stop"] = True

if __name__ == "__main__":
    main()
