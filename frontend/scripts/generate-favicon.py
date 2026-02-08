#!/usr/bin/env python3
"""
Generate favicon files from SVG source.
Creates .ico file and various PNG sizes for different platforms.
"""

import subprocess
import os
from pathlib import Path

# Directory paths
script_dir = Path(__file__).parent
public_dir = script_dir.parent / "public"
svg_file = public_dir / "favicon.svg"
output_dir = public_dir

# Ensure output directory exists
output_dir.mkdir(parents=True, exist_ok=True)

# Define favicon sizes
# ICO format supports multiple sizes embedded
ico_sizes = [16, 32, 48]
png_sizes = [16, 32, 48, 64, 128, 180, 192, 512]

def check_dependencies():
    """Check if required tools are installed."""
    try:
        subprocess.run(["convert", "-version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ImageMagick is not installed or 'convert' command is not available.")
        print("Please install ImageMagick:")
        print("  Ubuntu/Debian: sudo apt-get install imagemagick")
        print("  macOS: brew install imagemagick")
        print("  Or use an online converter to convert the SVG to ICO manually.")
        return False

def generate_png(size):
    """Generate PNG file of specific size from SVG."""
    output_file = output_dir / f"favicon-{size}x{size}.png"
    cmd = [
        "convert",
        "-background", "none",
        "-density", "300",
        str(svg_file),
        "-resize", f"{size}x{size}",
        str(output_file)
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✓ Generated {output_file.name}")
        return output_file
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to generate {output_file.name}: {e.stderr.decode()}")
        return None

def generate_ico():
    """Generate ICO file with multiple sizes embedded."""
    # First generate PNGs for ICO
    temp_pngs = []
    for size in ico_sizes:
        png_file = generate_png(size)
        if png_file:
            temp_pngs.append(png_file)

    if not temp_pngs:
        print("✗ Failed to generate ICO: no PNGs created")
        return

    # Combine PNGs into ICO
    ico_file = output_dir / "favicon.ico"
    cmd = ["convert"] + [str(p) for p in temp_pngs] + [str(ico_file)]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✓ Generated {ico_file.name}")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to generate ICO: {e.stderr.decode()}")

def generate_apple_touch_icon():
    """Generate apple-touch-icon.png (180x180)."""
    output_file = output_dir / "apple-touch-icon.png"
    cmd = [
        "convert",
        "-background", "none",
        "-density", "300",
        str(svg_file),
        "-resize", "180x180",
        str(output_file)
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✓ Generated {output_file.name}")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to generate apple-touch-icon: {e.stderr.decode()}")

def main():
    print("🎨 Generating favicon files from SVG...")
    print(f"Source: {svg_file}")
    print()

    if not svg_file.exists():
        print(f"✗ SVG file not found: {svg_file}")
        return

    if not check_dependencies():
        print("\n⚠️  Cannot generate favicons automatically.")
        print(f"The SVG file is available at: {svg_file}")
        print("You can use an online converter like:")
        print("  - https://convertio.co/svg-ico/")
        print("  - https://cloudconvert.com/svg-to-ico")
        return

    print("Generating ICO file...")
    generate_ico()
    print()

    print("Generating PNG files...")
    for size in png_sizes:
        if size not in ico_sizes:  # Skip sizes already generated
            generate_png(size)
    print()

    print("Generating Apple Touch Icon...")
    generate_apple_touch_icon()
    print()

    print("✅ Favicon generation complete!")
    print(f"Files saved to: {output_dir}")

if __name__ == "__main__":
    main()
