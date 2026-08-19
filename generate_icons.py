import os
from PIL import Image, ImageDraw

os.makedirs("static/icons", exist_ok=True)

def make_icon(size, filename):
    img = Image.new("RGBA", (size, size), (15, 23, 42, 255)) # Dark slate background #0f172a
    draw = ImageDraw.Draw(img)
    
    # Draw cyan/blue water circle background
    margin = size // 8
    draw.ellipse([margin, margin, size - margin, size - margin], fill=(14, 165, 233, 255))
    
    # Draw inner water drop / bottle shape
    cx, cy = size // 2, size // 2
    r = size // 4
    
    # Water drop top arc and bottom bulb
    draw.ellipse([cx - r, cy - r // 2, cx + r, cy + r * 1.2], fill=(255, 255, 255, 240))
    draw.polygon([(cx, cy - r * 1.3), (cx - r * 0.7, cy), (cx + r * 0.7, cy)], fill=(255, 255, 255, 240))
    
    img.save(filename, "PNG")
    print(f"Generated icon: {filename}")

make_icon(192, "static/icons/icon-192.png")
make_icon(512, "static/icons/icon-512.png")
