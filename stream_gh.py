# -*- coding: utf-8 -*-
"""Quizer jonli efir (GitHub Actions): v2 maket — barcha bloklar shisha kartalarda.
Statistika Beget dan SSH orqali, oqim RTMP orqali Telegram ga. Fon jonli animatsiyalanadi.
"""
import json, math, os, random as _rnd, subprocess, threading, time, unicodedata as _ud
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1920, 1080, 10
BASE = os.path.dirname(os.path.abspath(__file__))
SSH = ["ssh", "-i", os.environ.get("SSH_KEY_PATH", "key.pem"),
       "-o", "ConnectTimeout=12", "-o", "StrictHostKeyChecking=no",
       "-o", "BatchMode=yes", "-p", "22", os.environ.get("SSH_TARGET", ""),
       "timeout 40 php8.4 /home/g/grizzly26/qstats.php 2>/dev/null"]

FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def F(bold, size):
    return ImageFont.truetype(FB if bold else FR, size)

TITLE = (255, 255, 255); LABEL = (216, 205, 245); SUB = (196, 186, 232)
ACCENT = (192, 132, 252); ACCENT2 = (244, 114, 182); GOLD = (250, 204, 21); GREEN = (52, 211, 153)

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

def clean_name(n):
    n = _ud.normalize("NFKC", str(n or ""))
    n = "".join(ch for ch in n if _ud.category(ch)[0] in "LN" or ch in " .'-")
    return " ".join(n.split()) or "Foydalanuvchi"

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

def _tinted_bg(w, h):
    bg = Image.open(f"{BASE}/assets/bg.webp").convert("RGB").resize((w, h), Image.LANCZOS)
    ov = Image.new("RGB", (w, h), (96, 64, 190))
    return Image.blend(bg, ov, 74 / 255).convert("RGBA")

BG_BIG = _tinted_bg(2112, 1188)

def build_glass():
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    def glass(box, r=30, fill_a=28):
        x0, y0, x1, y1 = box
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sd = ImageDraw.Draw(sh)
        sd.rounded_rectangle([x0, y0 + 10, x1, y1 + 10], radius=r, fill=(0, 0, 0, 110))
        g.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)))
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        ld.rounded_rectangle(box, radius=r, fill=(255, 255, 255, fill_a),
                             outline=(255, 255, 255, 95), width=2)
        g.alpha_composite(layer)

    cells = [(56, 152), (522, 152), (988, 152), (1454, 152)]
    for (x, y) in cells:
        glass([x, y, x + 438, y + 156])
    glass([56, 332, 880, 480])                  # onlayn
    glass([56, 496, 880, 576], fill_a=44)       # bugun
    glass([56, 592, 880, 916])                  # oxirgi testlar
    glass([936, 332, 1864, 704])                # reyting
    glass([936, 720, 1864, 864])                # klasiko
    glass([1180, 888, 1864, 984], r=48, fill_a=40)  # imzo pill

    d = ImageDraw.Draw(g)
    for (x, y), col in zip(cells, [ACCENT, ACCENT2, GOLD, GREEN]):
        d.rounded_rectangle([x, y + 18, x + 9, y + 138], radius=4, fill=col + (255,))
    for (x, y), lab in zip(cells, ["FOYDALANUVCHILAR", "TESTLAR", "URINISHLAR", "SAVOLLAR"]):
        d.text((x + 32, y + 24), lab, font=F(True, 28), fill=LABEL + (255,))
    d.text((56, 30), "QUIZER", font=F(True, 60), fill=ACCENT + (255,))
    d.text((58, 98), "JONLI STATISTIKA EFIRI", font=F(True, 26), fill=SUB + (255,))
    d.text((1512, 36), "LIVE", font=F(True, 36), fill=TITLE + (255,))
    # onlayn karta statik matnlari
    d.text((156, 362), "HOZIR ONLAYN", font=F(True, 31), fill=LABEL + (255,))
    d.line([452, 356, 452, 456], fill=(255, 255, 255, 60), width=2)
    d.text((480, 362), "HOZIR YECHILMOQDA", font=F(True, 22), fill=SUB + (255,))
    # oxirgi testlar sarlavhasi
    d.text((88, 616), "OXIRGI TESTLAR", font=F(True, 30), fill=TITLE + (255,))
    d.rounded_rectangle([88, 664, 150, 670], radius=3, fill=ACCENT + (255,))
    # reyting sarlavhasi
    d.text((968, 356), "REYTING", font=F(True, 32), fill=TITLE + (255,))
    d.text((1832, 362), "TOP 3", font=F(True, 24), fill=GOLD + (255,), anchor="ra")
    d.rounded_rectangle([968, 404, 1030, 410], radius=3, fill=ACCENT + (255,))
    # klasiko
    d.text((1400, 736), "EL KLASIKO", font=F(True, 25), fill=GOLD + (255,), anchor="ma")
    d.text((1400, 768), "1 — 2", font=F(True, 48), fill=TITLE + (255,), anchor="ma")
    d.text((1400, 826), "Mbappé 41', 88'  •  Raphinha 61'", font=F(False, 21), fill=SUB + (255,), anchor="ma")
    b = barsa.resize((88, 88), Image.LANCZOS); r_ = real.resize((88, 88), Image.LANCZOS)
    g.paste(b, (972, 748), b); g.paste(r_, (1740, 748), r_)
    # imzo pill
    d.ellipse([1204, 908, 1268, 972], fill=ACCENT + (255,))
    d.text((1236, 940), "AH", font=F(True, 30), fill=(255, 255, 255, 255), anchor="mm")
    d.text((1288, 906), "Hakimov Azizbek", font=F(True, 29), fill=TITLE + (255,))
    d.text((1288, 944), "Full Stack dasturchi va tibbiyot talabasi", font=F(False, 22), fill=SUB + (255,))
    d.text((56, 1022), "devmed.uz/quizer", font=F(False, 24), fill=SUB + (255,))
    return g

GLASS = build_glass()

_r = _rnd.Random(42)
BUBBLES = [(_r.uniform(0, W), _r.uniform(0, H + 200), _r.uniform(6, 26), _r.uniform(14, 38)) for _ in range(22)]
_orb = Image.new("RGBA", (520, 520), (0, 0, 0, 0))
_od = ImageDraw.Draw(_orb)
_od.ellipse([60, 60, 460, 460], fill=(168, 110, 255, 52))
ORB = _orb.filter(ImageFilter.GaussianBlur(80))

def render(t):
    with stats_lock:
        s = dict(stats)
    ox = int(96 + 90 * math.sin(t * 2 * math.pi / 110))
    oy = int(54 + 48 * math.cos(t * 2 * math.pi / 140))
    img = BG_BIG.crop((ox, oy, ox + W, oy + H))
    img.paste(ORB, (int(1150 + 260 * math.sin(t * 2 * math.pi / 90)) - 260,
                    int(120 + 130 * math.cos(t * 2 * math.pi / 75)) - 260), ORB)
    img.paste(ORB, (int(180 + 200 * math.cos(t * 2 * math.pi / 120)) - 260,
                    int(560 + 120 * math.sin(t * 2 * math.pi / 95)) - 260), ORB)
    od = ImageDraw.Draw(img, "RGBA")
    for (bx, by, br, sp) in BUBBLES:
        yy = (by - t * sp) % (H + 160) - 80
        xx = bx + 14 * math.sin(t * 0.7 + by)
        od.ellipse([xx - br, yy - br, xx + br, yy + br], fill=(255, 255, 255, 26),
                   outline=(255, 255, 255, 70), width=2)
    img.alpha_composite(GLASS)
    d = ImageDraw.Draw(img, "RGBA")

    pulse = 0.55 + 0.45 * math.sin(t * 3.2)
    d.ellipse([1470, 40, 1500, 70], fill=(239, 68, 68, int(140 + 115 * pulse)))
    d.text((1864, 36), s.get("time_tashkent", "--:--"), font=F(True, 42), fill=TITLE + (255,), anchor="ra")
    d.text((1864, 86), s.get("date_tashkent", ""), font=F(False, 24), fill=SUB + (255,), anchor="ra")
    if not s:
        d.text((W // 2, 540), "Ma'lumot yuklanmoqda...", font=F(True, 44), fill=SUB + (255,), anchor="ma")
        return img.convert("RGB")
    tot, tod = s["totals"], s["today"]

    for (x, y), key in zip([(56, 152), (522, 152), (988, 152), (1454, 152)],
                           ["users", "tests", "attempts", "questions"]):
        d.text((x + 32, y + 62), fmt(anim(key, tot[key])), font=F(True, 72), fill=TITLE + (255,))

    # --- Onlayn ---
    cx, cy = 114, 410
    for ph in (0.0, 0.5):
        rr = 16 + 14 * ((t * 0.55 + ph) % 1.0)
        al = int(140 * (1 - ((t * 0.55 + ph) % 1.0)))
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=(52, 211, 153, max(al, 0)), width=3)
    d.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], fill=GREEN + (255,))
    on5 = s.get("online5", 0)
    num = fmt(anim("on5", on5, 0.2))
    d.text((156, 400), num, font=F(True, 60), fill=GREEN + (255,))
    nw = d.textlength(num, font=F(True, 60))
    d.text((156 + nw + 16, 428), "foydalanuvchi", font=F(False, 24), fill=SUB + (255,))
    solving = [x for x in (s.get("solving_now") or []) if str(x).strip()]
    if solving:
        cur = solving[int(t // 6) % len(solving)]
        d.text((480, 398), fit(d, clean_name(cur), F(True, 32), 350), font=F(True, 32), fill=TITLE + (255,))
        sub = f"va yana {len(solving) - 1} ta test yechilmoqda" if len(solving) > 1 else "test yechilmoqda"
        d.text((480, 438), sub, font=F(False, 24), fill=SUB + (255,))
    elif on5 == 0:
        try:
            hour = int(str(s.get("time_tashkent", "")).split(":")[0])
        except Exception:
            hour = -1
        if hour >= 23 or 0 <= hour < 7:
            d.text((480, 398), "Tungi rejim", font=F(True, 32), fill=GOLD + (255,))
            d.text((480, 438), "ertalab jonlanamiz", font=F(False, 24), fill=SUB + (255,))
        else:
            d.text((480, 398), "Hozir jimlik", font=F(True, 32), fill=TITLE + (255,))
            d.text((480, 438), "hech kim test yechmayapti", font=F(False, 24), fill=SUB + (255,))
    else:
        d.text((480, 398), "Faollik past", font=F(True, 32), fill=TITLE + (255,))
        d.text((480, 438), "hozircha test yechilmayapti", font=F(False, 24), fill=SUB + (255,))

    # --- Bugun ---
    line = (f"BUGUN:  +{tod['users']} yangi   •   {tod['tests']} test   •   "
            f"{tod['attempts']} urinish   •   {tod['uploads_done']} tayyor")
    f = F(True, 30)
    d.text((468, 520), fit(d, line, f, 780), font=f, fill=GREEN + (255,), anchor="ma")

    # --- Oxirgi testlar ---
    tests = s.get("recent_tests", [])[:4]
    ry = 692
    for j, tt in enumerate(tests):
        d.ellipse([96, ry + 12, 112, ry + 28], fill=ACCENT2 + (255,))
        d.text((132, ry), fit(d, tt["title"], F(False, 32), 700), font=F(False, 32), fill=TITLE + (255,))
        ry += 54
        if j < len(tests) - 1:
            d.line([96, ry - 12, 848, ry - 12], fill=(255, 255, 255, 40), width=1)

    # --- Reyting TOP-3 ---
    medals = [GOLD, (226, 232, 240), (251, 146, 60)]
    top_r = s.get("top_rating", [])
    if not top_r:
        d.text((968, 452), "Hozircha ma'lumot yo'q", font=F(False, 32), fill=SUB + (255,))
    ry = 428
    for i, u in enumerate(top_r[:3]):
        if i == 0:
            hl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            hd = ImageDraw.Draw(hl)
            hd.rounded_rectangle([956, ry - 8, 1844, ry + 72], radius=20, fill=(250, 204, 21, 30))
            img.alpha_composite(hl)
            d = ImageDraw.Draw(img, "RGBA")
        d.ellipse([968, ry, 1024, ry + 56], fill=medals[i] + (255,))
        d.text((996, ry + 28), str(i + 1), font=F(True, 30), fill=(40, 24, 8, 255), anchor="mm")
        d.text((1048, ry + 6), fit(d, clean_name(u.get("name", "")), F(True, 33), 470), font=F(True, 33), fill=TITLE + (255,))
        sc = fmt(u.get("score", 0))
        fw = d.textlength(" ball", font=F(False, 23))
        d.text((1832, ry + 16), " ball", font=F(False, 23), fill=SUB + (255,), anchor="ra")
        d.text((1832 - fw, ry + 6), sc, font=F(True, 36), fill=ACCENT + (255,), anchor="ra")
        ry += 92
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
           "-stream_loop", "-1", "-i", f"{BASE}/assets/loop.mp3",
           "-map", "0:v", "-map", "1:a",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast",
           "-b:v", "1700k", "-maxrate", "1900k", "-bufsize", "3400k", "-g", str(FPS * 2),
           "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
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
