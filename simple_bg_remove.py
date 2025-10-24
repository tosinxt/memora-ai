import sys
import subprocess
import os
from pathlib import Path

def remove_background(input_path, output_path=None):
    """Remove background using rembg CLI"""
    if output_path is None:
        output_path = str(Path(input_path).with_stem(f"{Path(input_path).stem}_nobg"))
    
    cmd = [
        "rembg", "i", 
        "-m", "u2net",
        "-a",  # Enable alpha matting
        "--alpha-matting-foreground-threshold", "240",
        "--alpha-matting-background-threshold", "10",
        "--alpha-matting-erode-size", "10",
        input_path,
        output_path
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"Background removed successfully. Output saved to: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error removing background: {e}")
        return None
    
    return output_path

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python simple_bg_remove.py <input_image> [output_image]")
        sys.exit(1)
    
    input_img = sys.argv[1]
    output_img = sys.argv[2] if len(sys.argv) > 2 else None
    
    remove_background(input_img, output_img)
