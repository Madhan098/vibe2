"""
Simple script to create PWA icons
Requires PIL/Pillow: pip install Pillow
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size):
    """Create an icon with the specified size"""
    # Create image with gradient background
    img = Image.new('RGB', (size, size), color='#6366f1')
    draw = ImageDraw.Draw(img)
    
    # Draw gradient-like effect (simplified)
    for i in range(size):
        ratio = i / size
        r = int(99 + (139 - 99) * ratio)
        g = int(102 + (92 - 102) * ratio)
        b = int(241 + (246 - 241) * ratio)
        draw.rectangle([(0, i), (size, i+1)], fill=(r, g, b))
    
    # Try to add emoji (may not work on all systems)
    try:
        # Use a large font
        font_size = int(size * 0.6)
        font = ImageFont.truetype("arial.ttf", font_size)
        text = "🧠"
        
        # Get text bounding box
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Center the text
        x = (size - text_width) // 2
        y = (size - text_height) // 2
        
        draw.text((x, y), text, fill='white', font=font)
    except:
        # Fallback: draw a simple circle
        margin = size // 4
        draw.ellipse([margin, margin, size - margin, size - margin], 
                    fill='white', outline='white', width=size//20)
    
    return img

def main():
    """Generate all required icon sizes"""
    sizes = [72, 96, 128, 144, 152, 192, 384, 512]
    
    print("Creating PWA icons...")
    for size in sizes:
        icon = create_icon(size)
        filename = f"icon-{size}x{size}.png"
        icon.save(filename)
        print(f"Created: {filename}")
    
    print("\nAll icons created successfully!")

if __name__ == "__main__":
    # Change to icons directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()

