#!/usr/bin/env python3
# Generate textures for T-Bone kart
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import random, math, os

out_dir = "/home/user/tbone_kart/tbone"
os.makedirs(out_dir, exist_ok=True)

# Helper to find font
def get_font(size, bold=False):
    # Try common fonts
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except:
                pass
    return ImageFont.load_default()

# --- steak texture 1024 ---
print("Generating steak_texture.png")
size = 1024
img = Image.new("RGB", (size,size), (90, 35, 28)) # base #5a2320
draw = ImageDraw.Draw(img)

# Add noise marbling
for _ in range(8000):
    x = random.randint(0,size-1)
    y = random.randint(0,size-1)
    r = random.randint(1,3)
    # fat marbling off-white
    col = random.choice([(232,216,195), (210,180,140), (110,50,40), (70,30,20)])
    # vary alpha by drawing circle
    draw.ellipse([x-r, y-r, x+r, y+r], fill=col)

# Add larger fat blobs
for _ in range(40):
    cx = random.randint(50, size-50)
    cy = random.randint(50, size-50)
    w = random.randint(20,80)
    h = random.randint(10,40)
    angle = random.randint(0,180)
    # draw ellipse blob of fat
    blob = Image.new("RGBA", (w*2,h*2), (0,0,0,0))
    bd = ImageDraw.Draw(blob)
    bd.ellipse([0,0,w*2,h*2], fill=(255,248,220, 180))
    blob = blob.rotate(angle, expand=True)
    bx = cx - blob.width//2
    by = cy - blob.height//2
    img.paste(blob, (bx,by), blob)

# Grill marks - diagonal dark stripes
for i in range(0, size, 40):
    # diagonal lines
    draw.line([(i- size, 0), (i, size)], fill=(20,5,5), width=6)
    draw.line([(i- size+10, 0), (i+10, size)], fill=(40,15,10), width=3)

img = img.filter(ImageFilter.GaussianBlur(radius=1.2))
# Enhance contrast slightly
img.save(os.path.join(out_dir, "steak_meat.png"))

# --- bone texture ---
print("Generating bone texture")
size2 = 512
bone = Image.new("RGB", (size2,size2), (255,248,220)) # cream
bd = ImageDraw.Draw(bone)
# subtle noise
for _ in range(2000):
    x = random.randint(0,size2-1)
    y = random.randint(0,size2-1)
    r = random.randint(1,2)
    bd.ellipse([x-r,y-r,x+r,y+r], fill=(245,235,200))
# add slight shadow at edges via gradient
for y in range(size2):
    factor = abs(y - size2//2) / (size2//2)
    darken = int(10*factor)
    # vertical gradient not needed
    pass
bone = bone.filter(ImageFilter.GaussianBlur(0.8))
bone.save(os.path.join(out_dir, "bone.png"))

# --- kart body ---
print("Generating kart body texture")
kart_tex = Image.new("RGB", (1024,1024), (26,5,0)) # #1a0500
draw = ImageDraw.Draw(kart_tex)
# gold racing stripes
# central double stripe gold
stripe_color = (196,164,132) # #c4a484 brass
# draw two vertical stripes (but kart UV will map roughly; horizontal stripe along length)
# We'll make horizontal stripes (since kart length along Y)
draw.rectangle([0, 440, 1024, 470], fill=stripe_color) # thin gold
draw.rectangle([0, 480, 1024, 540], fill=(90,15,10)) # red inner
draw.rectangle([0, 540, 1024, 570], fill=stripe_color)
# side accents
draw.rectangle([0, 300, 1024, 310], fill=stripe_color)
draw.rectangle([0, 710, 1024, 720], fill=stripe_color)
# Add carbon fiber pattern subtle
for y in range(0,1024, 8):
    for x in range(0,1024, 8):
        if (x+y)%16==0:
            kart_tex.putpixel((x,y), (30,8,4))

# Add T-BONE text in gold on sides
font_big = get_font(90, bold=True)
font_small = get_font(28, bold=True)
# T-BONE centered
text = "T-BONE"
# draw with outline
for dx,dy in [(-2,-2),(-2,2),(2,-2),(2,2)]:
    draw.text((512, 500), text, font=font_big, fill=(0,0,0), anchor="mm",)
draw.text((512,500), text, font=font_big, fill=(255,240,210), anchor="mm")

draw.text((512, 560), "STEAKHOUSE RACER", font=font_small, fill=(196,164,132), anchor="mm")

kart_tex = kart_tex.filter(ImageFilter.GaussianBlur(0.5))
kart_tex.save(os.path.join(out_dir, "kart_body.png"))

# separate kart chassis metal texture
chassis = Image.new("RGB", (1024,1024), (18,18,18)) # matte black
draw2 = ImageDraw.Draw(chassis)
# brushed metal lines
for y in range(0,1024, 4):
    shade = random.randint(12,22)
    draw2.line([(0,y),(1024,y)], fill=(shade,shade,shade))
# gold bolts pattern
for _ in range(60):
    x=random.randint(0,1024)
    y=random.randint(0,1024)
    draw2.ellipse([x-4,y-4,x+4,y+4], fill=(196,164,132), outline=(80,40,10))
chassis.save(os.path.join(out_dir, "kart_chassis.png"))

# --- wheel ---
print("Generating wheel")
wheel = Image.new("RGB", (512,512), (10,10,10))
wdraw = ImageDraw.Draw(wheel)
# rim - chrome gradient simulation
# outer tire black
wdraw.ellipse([10,10,502,502], fill=(5,5,5), outline=(20,20,20), width=4)
# chrome rim
wdraw.ellipse([90,90,422,422], fill=(200,200,205), outline=(255,255,255), width=2)
# inner hub
wdraw.ellipse([180,180,332,332], fill=(30,5,0), outline=(196,164,132), width=3)
# 5 lug nuts
cx,cy=256,256
for i in range(5):
    ang = i*72 * math.pi/180
    x = cx + math.cos(ang)*45
    y = cy + math.sin(ang)*45
    wdraw.ellipse([x-8,y-8,x+8,y+8], fill=(196,164,132), outline=(255,255,255))
# spokes - 5 star
for i in range(5):
    ang = i*72 * math.pi/180 + math.pi/5
    x1 = cx + math.cos(ang)*85
    y1 = cy + math.sin(ang)*85
    x2 = cx + math.cos(ang)*160
    y2 = cy + math.sin(ang)*160
    wdraw.line([(x1,y1),(x2,y2)], fill=(180,180,185), width=14)
    wdraw.line([(x1,y1),(x2,y2)], fill=(220,220,225), width=6)
wheel.save(os.path.join(out_dir, "wheel.png"))

wheel_gloss = Image.new("RGB", (512,512), (30,30,30))
wheel_gloss.save(os.path.join(out_dir, "wheel_gloss.png"))

# --- license plate ---
print("Generating license plate")
plate = Image.new("RGB", (512,256), (245,245,240))
pdraw = ImageDraw.Draw(plate)
# border
pdraw.rectangle([4,4,508,252], outline=(0,0,0), width=8)
pdraw.rectangle([12,12,500,244], outline=(196,164,132), width=4)
# text T-BONE
font_plate = get_font(110, bold=True)
pdraw.text((256, 105), "T-BONE", font=font_plate, fill=(15,5,5), anchor="mm")
# small text at bottom
font_small2 = get_font(22, bold=False)
pdraw.text((256,190), "STEAK • RACING", font=font_small2, fill=(80,10,10), anchor="mm")
# bolts
for x in [30, 482]:
    for y in [32, 224]:
        pdraw.ellipse([x-10,y-10,x+10,y+10], fill=(60,60,60), outline=(180,180,180))
plate.save(os.path.join(out_dir, "license_plate.png"))

# --- steering wheel ---
steer = Image.new("RGB", (512,512), (20,12,8))
sdraw = ImageDraw.Draw(steer)
# wood grain
for y in range(512):
    shade = int(30 + 15*math.sin(y*0.1) + random.randint(-5,5))
    sdraw.line([(0,y),(512,y)], fill=(shade+40, shade+20, shade))
# center badge
sdraw.ellipse([200,200,312,312], fill=(26,5,0), outline=(196,164,132), width=6)
font_badge = get_font(40, bold=True)
sdraw.text((256,256), "TB", font=font_badge, fill=(196,164,132), anchor="mm")
steer.save(os.path.join(out_dir, "steering.png"))

# --- headlight ---
headlight = Image.new("RGB", (256,256), (250,250,245))
hdraw = ImageDraw.Draw(headlight)
hdraw.ellipse([20,20,236,236], fill=(255,255,255), outline=(200,200,200), width=4)
# lens highlight
hdraw.ellipse([60,60,120,120], fill=(255,255,255))
hdraw.ellipse([70,70,110,110], fill=(240,240,255))
headlight.save(os.path.join(out_dir, "headlight.png"))

# --- seat ---
seat = Image.new("RGB", (512,512), (120,18,10))
sdraw2 = ImageDraw.Draw(seat)
for y in range(512):
    c = int(120 + 20*math.sin(y*0.05))
    sdraw2.line([(0,y),(512,y)], fill=(c, 18, 10))
# stitching
for x in [80, 432]:
    sdraw2.line([(x,0),(x,512)], fill=(196,164,132), width=3)
seat.save(os.path.join(out_dir, "seat.png"))

# --- exhaust metal ---
exhaust_tex = Image.new("RGB", (512,512), (40,40,42))
edraw = ImageDraw.Draw(exhaust_tex)
for y in range(0,512,6):
    shade = 40 + int(10*math.sin(y*0.2))
    edraw.line([(0,y),(512,y)], fill=(shade,shade,shade+2))
exhaust_tex.save(os.path.join(out_dir, "exhaust.png"))

# --- shadow ---
print("Generating shadow")
shadow = Image.new("RGBA", (256,256), (0,0,0,0))
sdraw3 = ImageDraw.Draw(shadow)
# ellipse shadow
sdraw3.ellipse([20,60,236,200], fill=(0,0,0,110))
# blur
shadow = shadow.filter(ImageFilter.GaussianBlur(12))
# save as RGB with alpha
shadow.save(os.path.join(out_dir, "tbone_shadow.png"))

# --- icon 128x128 ---
print("Generating icon")
icon = Image.new("RGBA", (128,128), (26,5,0,255))
idraw = ImageDraw.Draw(icon)
# draw steak silhouette simplified
# Use polygon approximated
# steak outline points scaled to 128
# We'll reuse steak norm points to draw
import json
# load steak outline if exists
try:
    steak_pts = json.loads(open('/tmp/steak_outline.json').read())
    # map to 128x128
    poly = []
    for x,y in steak_pts:
        px = 64 + x*55*2.2 # scale
        py = 64 - y*55*2.2 # y inverted back to image
        poly.append((px,py))
    idraw.polygon(poly, fill=(90,35,28), outline=(255,255,255), width=3)
    # inner T
    t_pts = json.loads(open('/tmp/tbone_t.json').read())
    t_poly=[]
    for x,y in t_pts:
        px = 64 + x*55*2.2
        py = 64 - y*55*2.2
        t_poly.append((px,py))
    idraw.polygon(t_poly, fill=(255,248,220), outline=(255,255,255), width=1)
except Exception as e:
    print("icon steak failed",e)
    # fallback simple
    idraw.ellipse([20,20,108,108], fill=(90,35,28), outline=(255,255,255), width=4)

# Add border
idraw.rectangle([0,0,127,127], outline=(196,164,132), width=3)
# text T?
font_icon = get_font(14, bold=True)
idraw.text((64,115), "T-BONE", font=font_icon, fill=(255,240,210), anchor="mm")
icon.save(os.path.join(out_dir, "tbone_icon.png"))

# minimap same
icon.save(os.path.join(out_dir, "tbone_minimap.png"))

# --- gloss maps ---
# simple white for gloss
for name in ["kart_body_gloss.png", "chassis_gloss.png", "steak_gloss.png"]:
    gloss = Image.new("RGB", (256,256), (60,60,60))
    gdraw = ImageDraw.Draw(gloss)
    # subtle highlight
    gdraw.ellipse([40,40,220,220], fill=(120,120,120))
    gloss.save(os.path.join(out_dir, name))

print("All textures generated in", out_dir)
ls = os.listdir(out_dir)
print(ls)
