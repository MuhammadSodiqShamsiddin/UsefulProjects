import colorama.win32
from vpython import *
from math import sin, cos, pi, sqrt, atan2

# ══════════════════════════════════════════════════════════════════════
#  SAHNA
# ══════════════════════════════════════════════════════════════════════
screen = canvas(
    title="<b>Chorak (λ/4) va yarim (λ/2) to'lqin plastinkalar — 3D Simulyator</b>",
    width=1520, height=600
)
screen.background = color.gray(0.55)
screen.center  = vec(0, 82, 0)
screen.range   = 540
screen.forward = vec(0.10, -0.12, -1)
screen.autoscale = False

# -----------------------------
# 2. FOKUSNI TANLASH FUNKSIYASI
# -----------------------------
def fokusni_kochir(maqsad_pos):
    """Kamera markazini (screen.center) maqsad_pos ga silliq siljitadi."""
    qadam_soni = 50
    qadam_vektor = (maqsad_pos - screen.center) / qadam_soni
    for _ in range(qadam_soni):
        rate(30)
        screen.center += qadam_vektor
    screen.center = maqsad_pos

def sichqon_bosildi(voqea):
    tanlangan = screen.mouse.pick
    if tanlangan is not None:
        fokusni_kochir(tanlangan.pos)
        print(f"Fokus {tanlangan.pos} ga o‘zgartirildi")

screen.bind('click', sichqon_bosildi)
# ══════════════════════════════════════════════════════════════════════
#  FIZIKA DOIMIYLARI
# ══════════════════════════════════════════════════════════════════════
AMP   = 18
LAMB  = 578/6.56
K     = 2 * pi / LAMB
OMEGA = 2 * pi * 1.4
Y0    = 90        # optik o'q balandligi

# X-koordinatalar
XL  = -400        # Lampa
XF  = -358        # Filtr
XP  = -192        # Polyarizator
XW  =   10        # To'lqin plastinkasi
XA  =  210        # Analizator
XD  =  248        # Detektor (analizatorga yopishib turadi)
MMX =  338        # Multimetr

# ══════════════════════════════════════════════════════════════════════
#  HOLAT
# ══════════════════════════════════════════════════════════════════════
state = {'pol': 0, 'wtype': 'q', 'wplate': 45, 'ana': 0}

# ══════════════════════════════════════════════════════════════════════
#  JONES MATRISA HISOBI
# ══════════════════════════════════════════════════════════════════════
def jones(pol_d, wp_d, wtype):
    """
    Polyarizator va to'lqin plastinkasidan o'tgandan keyin E vektori.
    Qaytaradi: (Ey_amp, Ey_faza, Ez_amp, Ez_faza)
    """
    th = pol_d * pi / 180
    ph = wp_d  * pi / 180
    Ey0, Ez0 = cos(th), sin(th)

    if wtype == 'none':
        return (abs(Ey0), 0.0 if Ey0 >= 0 else pi,
                abs(Ez0), 0.0 if Ez0 >= 0 else pi)

    d = pi / 2 if wtype == 'q' else pi   # faza farqi

    Ef =  Ey0 * cos(ph) + Ez0 * sin(ph)
    Es = -Ey0 * sin(ph) + Ez0 * cos(ph)

    Ey_re = Ef * cos(ph) - Es * cos(d) * sin(ph)
    Ey_im =              - Es * sin(d) * sin(ph)
    Ez_re = Ef * sin(ph) + Es * cos(d) * cos(ph)
    Ez_im =                Es * sin(d) * cos(ph)

    Eya = sqrt(Ey_re**2 + Ey_im**2)
    Eza = sqrt(Ez_re**2 + Ez_im**2)
    Eyp = atan2(Ey_im, Ey_re) if Eya > 1e-5 else 0.0
    Ezp = atan2(Ez_im, Ez_re) if Eza > 1e-5 else 0.0
    return Eya, Eyp, Eza, Ezp


def intensity(Eya, Eyp, Eza, Ezp, ana_d):
    """
    Vaqtga o'rtacha intensivlik: [0, 1].
    I = ½(Ey·cosα)² + ½(Ez·sinα)² + Ey·Ez·cosα·sinα·cos(φy−φz)
    """
    al = ana_d * pi / 180
    ca, sa = cos(al), sin(al)
    I = (0.5 * (Eya * ca)**2
       + 0.5 * (Eza * sa)**2
       + Eya * Eza * ca * sa * cos(Eyp - Ezp))
    return max(0.0, min(1.0, I * 2.0))


def classify(st):
    if st['wtype'] == 'none': return "Chiziqli qutblanish"
    if st['wtype'] == 'h':    return "Chiziqli qutblanish  (λ/2 — burilgan)"
    diff = abs((st['wplate'] - st['pol']) % 180)
    if diff < 5 or abs(diff - 90) < 5: return "Chiziqli qutblanish"
    if 42 < diff < 48:                 return "Doiraviy qutblanish  ◉"
    return "Elliptik qutblanish"

# ══════════════════════════════════════════════════════════════════════
#  OPTIK STOL ASOSI
# ══════════════════════════════════════════════════════════════════════
box(pos=vec(-60, -7, 0), size=vec(950, 8, 88), color=color.gray(0.81))
for z in (-23, 23):
    box(pos=vec(-55, -2, z), size=vec(945, 3, 5), color=color.gray(0.55))

# ══════════════════════════════════════════════════════════════════════
#  DISK KOMPONENT YARATISH
#  Ko'rsatgich: TASHQI YUZADA (radius 30+, disk ichida emas!)
# ══════════════════════════════════════════════════════════════════════
def mk_disk(xpos, lens_col, txt):
    cp = vec(xpos, Y0, 0)

    # Tashqi halqa (qoramtir, metall faktura)
    ring(pos=cp, axis=vec(1, 0, 0),
         radius=30, thickness=5.5, color=color.gray(0.17))

    # Gradus belgi chiziqlar (10°da bir, 30°da uzunroq)
    for deg in range(0, 360, 10):
        ang = deg * pi / 180
        r  = 28.5 if deg % 30 == 0 else 27.0
        sz = vec(0.5, 3.8 if deg % 30 == 0 else 2.0, 0.9)
        box(pos=vec(xpos, cp.y + r * cos(ang), r * sin(ang)),
            size=sz,
            color=color.white if deg % 30 == 0 else color.gray(0.58))

    # Raqam belgilari (0, 30, 60, 90)
    for deg in (0, 30, 60, 90):
        ang = deg * pi / 180
        label(pos=vec(xpos, cp.y + 36 * cos(ang), 36 * sin(ang)),
              text=str(deg), height=8, color=color.white, box=False, opacity=0)

    # Markaziy optik element
    lens = cylinder(pos=vec(xpos - 3, cp.y, 0), axis=vec(6, 0, 0),
                   radius=25, color=lens_col, opacity=0.40, shininess=0.95)

    # ─── SARIQ KO'RSATGICH — DISK TASHQI YUZASIDA ───
    # Halqa radiusi = 30. Ko'rsatgich 30–38 oraliqda (tashqarida) joylashadi.
    ind = box(
        pos=cp + vec(0, 40, 0),  # disk tashqarisida, biroz balandroq
        size=vec(2, 16, 6),  # parallelopiped shakli
        color=color.yellow
    )

    # Qizil optik o'q (faqat plastinka uchun, buriladi)
    oax = cylinder(pos=cp - vec(0, 12, 0), axis=vec(0, 24, 0),
                  radius=0.9, color=color.red, opacity=0.75)

    # Oyoq
    cylinder(pos=vec(xpos, cp.y - 27, 0), axis=vec(0, -70, 0),
            radius=4.5, color=color.gray(0.40))
    box(pos=vec(xpos, -5, 0), size=vec(18, 6, 54), color=color.gray(0.40))

    # Yorliq
    lbl = label(pos=vec(xpos, -112, 0), text=txt, height=11,
               color=color.white, box=False, opacity=0, align='center')

    return {'lens': lens, 'ind': ind, 'oax': oax, 'lbl': lbl, 'cp': cp}


def set_ind(d, ang_deg):
    ang   = ang_deg * pi / 180
    r_rim = 42      # disk tashqi radiusidan biroz yuqori
    d['ind'].pos = d['cp'] + vec(0, r_rim * cos(ang), r_rim * sin(ang))
    d['ind'].up  = vec(0, cos(ang), sin(ang))   # tutqich radial yo'nalishda tik turadi


def set_oax(d, ang_deg):
    """Qizil optik o'q yo'nalishini yangilash."""
    ang = ang_deg * pi / 180
    R   = 12
    d['oax'].pos  = d['cp'] - vec(0, R * cos(ang), R * sin(ang))
    d['oax'].axis = vec(0, 2 * R * cos(ang), 2 * R * sin(ang))

# ══════════════════════════════════════════════════════════════════════
#  LAMPA BLOKI (rasmdagiga o'xshash quti + kondensor + ventilatsiya)
# ══════════════════════════════════════════════════════════════════════
# Asosiy quti
box(pos=vec(XL, Y0, 0),      size=vec(56, 38, 52), color=color.gray(0.22))
# Ventilatsiya tirqishlari (ustki qism, rasmdagidek)
for dz in range(-20, 22, 7):
    box(pos=vec(XL, Y0 + 21, dz), size=vec(56, 1.8, 3.5), color=color.gray(0.11))
# Kondensor linza / old yuz
ring(pos=vec(XL + 29, Y0, 0), axis=vec(1, 0, 0),
     radius=9.5, thickness=3, color=color.gray(0.38))
cylinder(pos=vec(XL + 27, Y0, 0), axis=vec(4, 0, 0),
        radius=12, color=vec(0.85, 0.92, 1.0), opacity=0.28)
# Yorug'lik manbai (ichida)
sphere(pos=vec(XL + 27, Y0, 0), radius=8, color=color.orange, emissive=True)
# Kabel ulash (orqa)
box(pos=vec(XL - 36, Y0, 0), size=vec(16, 22, 24), color=color.gray(0.28))
for yy in (6, -6):
    cylinder(pos=vec(XL - 36, Y0 + yy, 0), axis=vec(8, 0, 0),
            radius=2.8, color=color.gray(0.42))
# Oyoq
cylinder(pos=vec(XL, Y0-18, 0), axis=vec(0, -74, 0),
        radius=4.5, color=color.gray(0.42))
box(pos=vec(XL, -5, 0), size=vec(18, 6, 58), color=color.gray(0.42))
label(pos=vec(XL, -112, 0), text="Galogen lampa\n6 V / 30 W",
      height=10, color=color.white, box=False, opacity=0)

# Transformator (chapda, kabeI bilan)
TRX = XL - 82
box(pos=vec(TRX, Y0 - 24, 0), size=vec(48, 36, 40), color=color.gray(0.19))
box(pos=vec(TRX, Y0 - 7,  0), size=vec(48, 4, 40),  color=color.gray(0.26))
cylinder(pos=vec(TRX, Y0 - 7, 0), axis=vec(49, 0, 0), radius=6, color=color.gray(0.22))
cylinder(pos=vec(TRX, 55, 0), axis=vec(0, -60, 0), radius=4, color=color.gray(0.42))
box(pos=vec(TRX, -5, 0), size=vec(16, 6, 45), color=color.gray(0.42))
label(pos=vec(TRX, -112, 0), text="Transformator\n6/12 V",
      height=9, color=color.gray(0.58), box=False, opacity=0)
# Kabellar: transformator → lampa
for rc, zz in ((color.red, 6), (color.blue, -6)):
    pts = [vec(TRX + 24, Y0 - 7, zz),
           vec(TRX + 24, Y0 + 18, zz),
           vec(XL - 28,  Y0 + 18, zz),
           vec(XL - 28,  Y0,      zz)]
    curve(pts, color=rc, radius=1.3)

# ══════════════════════════════════════════════════════════════════════
#  FILTR (sariq plyonka)
# ══════════════════════════════════════════════════════════════════════
box(pos=vec(XF, Y0, 0), size=vec(5, 37, 37),
    color=color.yellow, opacity=0.55, shininess=1.0)
for z in (-14, 14):
    cylinder(pos=vec(XF - 18, Y0, z), axis=vec(16, 0, 0),
            radius=2.2, color=color.gray(0.30))
label(pos=vec(XF, -112, 0), text="Filtr",
      height=10, color=color.white, box=False, opacity=0)
cylinder(pos = vec(-360, Y0, 0), axis = vec(570, 0, 0), radius = 0.5, color = color.yellow)

# ══════════════════════════════════════════════════════════════════════
#  UCHTA DISK
# ══════════════════════════════════════════════════════════════════════
dp = mk_disk(XP, color.blue, "Polyarizator\nθ_P = 0°")
dw = mk_disk(XW, color.cyan, "λ/4 Plastinka\nφ = 45°")
da = mk_disk(XA, color.blue, "Analizator\nα = 0°")

set_ind(dp, 0);  set_ind(dw, 45);  set_ind(da, 0)
set_oax(dw, 45)
dp['oax'].visible = False
da['oax'].visible = False

# ══════════════════════════════════════════════════════════════════════
#  DETEKTOR — analizatorga YOPISHIB turadi
#  Ulovchi gilza + detektor qutisi ketma-ket
# ══════════════════════════════════════════════════════════════════════
# Ulovchi gilza (analizator diski → detektor)
# Analizator diski: markaz XA=210, qalinlik ~6 → old yuz x≈213
# Gilza: markaz 222, kenglik 20 → 212–232
cylinder(pos=vec(XA+4, Y0, 0), radius = 12, axis=vec(50, 0, 0), color=color.gray(0.27))

# Detektor tanasi: markaz XD=248, kenglik 28 → 234–262
# Gilza right edge 232, detektor left edge 234 → ~2 birlik oraliq ✓
#box(pos=vec(XD, Y0, 0), size=vec(28, 28, 28), color=color.gray(0.20))
# Ulagich pinlar (orqasida)
for yy in (7, -7):
    cylinder(pos=vec(XD + 14, Y0 + yy, 0), axis=vec(9, 0, 0),
            radius=2.2, color=color.gray(0.50))
# Oyoq
cylinder(pos=vec(XD, Y0 - 11, 0), axis=vec(0, -84, 0),
        radius=4.0, color=color.gray(0.42))
box(pos=vec(XD, -5, 0), size=vec(14, 6, 40), color=color.gray(0.42))
label(pos=vec(XD, -112, 0), text="Fotoelement\n(Si detektor)",
      height=10, color=color.white, box=False, opacity=0)

# ══════════════════════════════════════════════════════════════════════
#  MULTIMETR (PeakTech 3340 — ko'k rang)
# ══════════════════════════════════════════════════════════════════════
box(pos=vec(MMX, Y0 + 2,  0), size=vec(16, 64, 52), color=vec(0.10, 0.16, 0.44))
box(pos=vec(MMX, Y0 + 35, 0), size=vec(16, 5,  52), color=vec(0.13, 0.20, 0.54))
# LCD displey
box(pos=vec(MMX + 8.5, Y0 + 18, 0), size=vec(1.2, 25, 38), color=color.black)
# Aylanuvchi selektor
cylinder(pos=vec(MMX, Y0 - 14, 0), axis=vec(17, 0, 0), radius=7.5, color=vec(0.08,0.13,0.38))
cylinder(pos=vec(MMX, Y0 - 14, 0), axis=vec(17, 0, 0), radius=3.0, color=color.gray(0.52))
# Oyoq
cylinder(pos=vec(MMX, Y0 - 27, 0), axis=vec(0, -70, 0), radius=4, color=color.gray(0.42))
box(pos=vec(MMX, -5, 0), size=vec(16, 6, 52), color=color.gray(0.42))
label(pos=vec(MMX, -112, 0), text="PeakTech 3340\nMultimetr",
      height=10, color=color.white, box=False, opacity=0)

# Kabellar (qizil va ko'k: detektor → multimetr)
for kc, yy in ((color.red, 6), (color.blue, -6)):
    pts = [vec(XD + 18, Y0 + yy, 0),
           vec(XD + 42, Y0 + yy, 0),
           vec(MMX - 9, Y0 + yy, 0)]
    curve(pts, color=kc, radius=1.4)
    cylinder(pos=vec(MMX - 9, Y0 + yy, 0), axis=vec(10, 0, 0),
            radius=2.4, color=kc)

# Displey belgilari
mm_disp = label(pos=vec(MMX + 9, Y0 + 21, 0), text="40.0",
               height=14, color=color.green, box=False, opacity=0,
               align='center', font='monospace')
label(pos=vec(MMX + 9, Y0 + 8,  0), text="μA  DC",
      height=8, color=vec(0, 0.52, 0), box=False, opacity=0)
label(pos=vec(MMX, Y0 + 31, 0), text="PeakTech",
      height=7, color=color.gray(0.66), box=False, opacity=0)
label(pos=vec(MMX, Y0 + 24, 0), text="3340 DMM",
      height=6, color=color.gray(0.52), box=False, opacity=0)

# ══════════════════════════════════════════════════════════════════════
#  TO'LQIN KURVALARI VA STRELKALAR
# ══════════════════════════════════════════════════════════════════════
STEP = 1

def xlist(x0, x1, mg=10):
    xs, x = [], x0 + mg
    while x < x1 - mg:
        xs.append(x); x += STEP
    return xs

xs_n = xlist(XL + 34, XP+10,  8)
xs_l = xlist(XP-6,  XW+4,  6)
xs_m = xlist(XW + 5,  XA+10,  6)

# ─── 1. TABIIY NUR: 4 tekislik × 45° ───
# Fizikaga to'g'ri: tabiiy nurda teng ehtimollik bilan barcha
# NANG — 8 tekislik, 22.5° oraliq
import colorsys
NANG = [i * pi / 4 for i in range(8)]
NCOL = [vec(*colorsys.hsv_to_rgb(i/8, 0.9, 1.0)) for i in range(8)]

nat_cvs = []
nat_arrs = []   # ← yangi

for c_col, b_ang in zip(NCOL, NANG):
    c = curve(radius=0.35, color=color.yellow, opacity=0.85)
    for xi in xs_n:
        c.append(vec(xi, Y0, 0))
    nat_cvs.append((c, b_ang))

    # Har tekislik uchun strelkalar (har 8-nuqtada)
    arrs = []
    for j, xi in enumerate(xs_n):
        if j % 8 == 0:
            # + yo'nalish
            arrs.append(arrow(
                pos=vec(xi, Y0, 0),
                axis=vec(0, AMP * 0.5 * cos(b_ang), AMP * 0.5 * sin(b_ang)),
                shaftwidth=0.4, headwidth=1.4, headlength=1.8,
                color=color.red, opacity=0.75
            ))
            # − yo'nalish (qarama-qarshi)
            arrs.append(arrow(
                pos=vec(xi, Y0, 0),
                axis=vec(0, -AMP * 0.5 * cos(b_ang), -AMP * 0.5 * sin(b_ang)),
                shaftwidth=0.4, headwidth=1.4, headlength=1.8,
                color=color.red, opacity=0.75
            ))
    nat_arrs.append((arrs, b_ang))

# ─── 2. CHIZIQLI: pol → plate ───
lin_cv = curve(radius=0.52, color=color.yellow)
for xi in xs_l: lin_cv.append(vec(xi, Y0, 0))
lin_arr = [arrow(pos=vec(xi, Y0, 0), axis=vec(0, AMP, 0),
                shaftwidth=0.55, headwidth=1.9, headlength=2.3, color=color.red)
           for j, xi in enumerate(xs_l) if j % 6 == 0]

# ─── 3. O'ZGARTIRILGAN: plate → ana (elliptik/doiraviy/chiziqli) ───
mod_cv = curve(radius=0.52, color=color.yellow)
for xi in xs_m: mod_cv.append(vec(xi, Y0, 0))
mod_arr = [arrow(pos=vec(xi, Y0, 0), axis=vec(0, AMP, 0),
                shaftwidth=0.55, headwidth=1.9, headlength=2.3, color=color.red)
           for j, xi in enumerate(xs_m) if j % 6 == 0]

# ══════════════════════════════════════════════════════════════════════
#  3D HOLAT BELGILARI
# ══════════════════════════════════════════════════════════════════════
lbl_pk  = label(pos=vec((XW + XA) // 2, Y0 + 98, 0),
               text="Doiraviy qutblanish  ◉",
               height=13, color=vec(0.4, 1.0, 0.5), box=False, opacity=0)
lbl_pol = label(pos=vec(XP, Y0 + 72, 0), text="θ_P = 0°",
               height=11, color=color.yellow, box=False, opacity=0)
lbl_wp  = label(pos=vec(XW, Y0 + 80, 0), text="λ/4 | φ = 45°",
               height=11, color=color.cyan,   box=False, opacity=0)
lbl_an  = label(pos=vec(XA, Y0 + 72, 0), text="α = 0°",
               height=11, color=color.yellow, box=False, opacity=0)
lbl_I   = label(pos=vec((XD + MMX) // 2, Y0 + 68, 0), text="I = 40.0 μA",
               height=12, color=color.orange, box=False, opacity=0)

# ══════════════════════════════════════════════════════════════════════
#  LABEL YANGILASH
# ══════════════════════════════════════════════════════════════════════
def update_labels():
    wn = {'none': "Plastinkasiz", 'q': "λ/4", 'h': "λ/2"}[state['wtype']]
    lbl_pol.text   = f"θ_P = {state['pol']}°"
    lbl_wp.text    = f"{wn} | φ = {state['wplate']}°"
    lbl_an.text    = f"α = {state['ana']}°"
    dp['lbl'].text = f"Polyarizator\nθ_P = {state['pol']}°"
    dw['lbl'].text = f"{wn} plastinka\nφ = {state['wplate']}°"
    da['lbl'].text = f"Analizator\nα = {state['ana']}°"
    cols = {'none': color.gray(0.5), 'q': color.cyan, 'h': vec(0.3, 1.0, 0.4)}
    dw['lens'].color  = cols[state['wtype']]
    dw['oax'].visible = (state['wtype'] != 'none')

# ══════════════════════════════════════════════════════════════════════
#  CALLBACK FUNKSIYALAR
#  (sl_pol, sl_wp, sl_ana, pol_txt, wp_txt, ana_txt — pastda yaratiladi;
#   Python closures: chaqirilganda mavjud bo'ladi)
# ══════════════════════════════════════════════════════════════════════
def on_pol(s):
    state['pol'] = int(s.value) % 360
    pol_txt.text = f"  {state['pol']:3d}°"
    set_ind(dp, state['pol']); update_labels()

def on_wp(s):
    state['wplate'] = int(s.value) % 180
    wp_txt.text = f"  {state['wplate']:3d}°"
    set_ind(dw, state['wplate']); set_oax(dw, state['wplate']); update_labels()

def on_ana(s):
    state['ana'] = int(s.value) % 360
    ana_txt.text = f"  {state['ana']:3d}°"
    set_ind(da, state['ana']); update_labels()

def pol_m(b):
    state['pol'] = (state['pol'] - 1) % 360
    sl_pol.value = state['pol']; pol_txt.text = f"  {state['pol']:3d}°"
    set_ind(dp, state['pol']); update_labels()

def pol_p(b):
    state['pol'] = (state['pol'] + 1) % 360
    sl_pol.value = state['pol']; pol_txt.text = f"  {state['pol']:3d}°"
    set_ind(dp, state['pol']); update_labels()

def wp_m(b):
    state['wplate'] = (state['wplate'] - 1) % 180
    sl_wp.value = state['wplate']; wp_txt.text = f"  {state['wplate']:3d}°"
    set_ind(dw, state['wplate']); set_oax(dw, state['wplate']); update_labels()

def wp_p(b):
    state['wplate'] = (state['wplate'] + 1) % 180
    sl_wp.value = state['wplate']; wp_txt.text = f"  {state['wplate']:3d}°"
    set_ind(dw, state['wplate']); set_oax(dw, state['wplate']); update_labels()

def ana_m(b):
    state['ana'] = (state['ana'] - 1) % 360
    sl_ana.value = state['ana']; ana_txt.text = f"  {state['ana']:3d}°"
    set_ind(da, state['ana']); update_labels()

def ana_p(b):
    state['ana'] = (state['ana'] + 1) % 360
    sl_ana.value = state['ana']; ana_txt.text = f"  {state['ana']:3d}°"
    set_ind(da, state['ana']); update_labels()

def s_none(b): state['wtype'] = 'none'; update_labels()
def s_q(b):    state['wtype'] = 'q';    update_labels()
def s_h(b):    state['wtype'] = 'h';    update_labels()

# ══════════════════════════════════════════════════════════════════════
#  BOSHQARUV PANELI
#  Slayder (surgich) + ±10° tugma har bir parametr uchun
# ══════════════════════════════════════════════════════════════════════
screen.append_to_caption("\n\n")
screen.append_to_caption(" <b>Polyarizator θ_P :</b>  ")
sl_pol  = slider(min=0,   max=360, value=0,  step=1, length=215, bind=on_pol)
pol_txt = wtext(text="    0°")
screen.append_to_caption("  ")
button(text=" ◄ −1° ", bind=pol_m)
button(text=" +1° ► ", bind=pol_p)

screen.append_to_caption("\n ")
screen.append_to_caption(" <b>Plastinka  φ :  </b>  ")
sl_wp   = slider(min=0,   max=180, value=45, step=1, length=215, bind=on_wp)
wp_txt  = wtext(text="   45°")
screen.append_to_caption("  ")
button(text=" ◄ −1° ", bind=wp_m)
button(text=" +1° ► ", bind=wp_p)

screen.append_to_caption("\n ")
screen.append_to_caption(" <b>Analizator α :  </b>  ")
sl_ana  = slider(min=0,   max=360, value=0,  step=1, length=215, bind=on_ana)
ana_txt = wtext(text="    0°")
screen.append_to_caption("  ")
button(text=" ◄ −1° ", bind=ana_m)
button(text=" +1° ► ", bind=ana_p)

screen.append_to_caption("\n\n ")
screen.append_to_caption(" <b>Plastinka turi :</b>  ")
button(text="   Yo'q   ", bind=s_none)
button(text="    λ/4   ", bind=s_q)
button(text="    λ/2   ", bind=s_h)
screen.append_to_caption("&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
                         " <b>Fotoelement toki :</b>  ")
tok_wt = wtext(text=" 40.0 μA ")

# ══════════════════════════════════════════════════════════════════════
#  ASOSIY ANIMATSIYA SIKLI
# ══════════════════════════════════════════════════════════════════════
t = 0
while True:
    rate(75)
    t += 1 / 75.0

    pol_r = state['pol']    * pi / 180
    ana_r = state['ana']    * pi / 180

    Eya, Eyp, Eza, Ezp = jones(state['pol'], state['wplate'], state['wtype'])
    I_val = intensity(Eya, Eyp, Eza, Ezp, state['ana'])
    sI    = sqrt(max(0.0, I_val))

    pk = classify(state)
    lbl_pk.text  = pk
    lbl_pk.color = (vec(.4, 1, .5) if "Doiraviy" in pk else
                    (color.cyan    if "Elliptik" in pk else color.yellow))

    I_ua = I_val * 80.0            # 80 μA = maksimal tok
    lbl_I.text    = f"I = {I_ua:.1f} μA"
    mm_disp.text  = f"{I_ua:.1f}"
    mm_disp.color = color.yellow if I_ua > 60 else vec(0, 1, 0)
    tok_wt.text   = f"  {I_ua:.1f} μA  "

    # ── 1. Tabiiy nur: 4 tekislik, 45° oraliq ──────────────────────
    for c, b in nat_cvs:
        for i, xi in enumerate(xs_n):
            ph = K * xi - OMEGA * t
            c.modify(i, pos=vec(xi,
                                Y0 + AMP * sin(ph) * cos(b),
                                AMP * sin(ph) * sin(b)))

    for arrs, b in nat_arrs:
        ai = 0
        for j, xi in enumerate(xs_n):
            if j % 8 == 0 and ai + 1 < len(arrs):
                ph = K * xi - OMEGA * t
                amp_val = AMP * sin(ph)
                arrs[ai].axis = vec(0, amp_val * cos(b), amp_val * sin(b))
                arrs[ai + 1].axis = vec(0, -amp_val * cos(b), -amp_val * sin(b))
                ai += 2

    # ── 2. Chiziqli: pol → plate ────────────────────────────────────
    ai = 0
    for i, xi in enumerate(xs_l):
        ph = K * xi - OMEGA * t
        vy = AMP * sin(ph) * cos(pol_r)
        vz = AMP * sin(ph) * sin(pol_r)
        lin_cv.modify(i, pos=vec(xi, Y0 + vy, vz))
        if i % 6 == 0 and ai < len(lin_arr):
            lin_arr[ai].axis = vec(0, vy, vz); ai += 1

    # ── 3. O'zgartirilgan: plate → ana (Jones natijasi) ─────────────
    ai = 0
    for i, xi in enumerate(xs_m):
        ph = K * xi - OMEGA * t
        vy = AMP * Eya * sin(ph + Eyp)
        vz = AMP * Eza * sin(ph + Ezp)
        mod_cv.modify(i, pos=vec(xi, Y0 + vy, vz))
        if i % 6 == 0 and ai < len(mod_arr):
            mod_arr[ai].axis = vec(0, vy, vz); ai += 1
