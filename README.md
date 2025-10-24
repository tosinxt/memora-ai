# Background Remover Engine

A Python-based background removal tool using deep learning models. This tool can remove backgrounds from single images or batch process entire directories.

## Features

- Remove background from single images or batch process multiple images
- Multiple model support (u2net, u2netp, u2net_human_seg, etc.)
- Optional alpha matting for better edge refinement
- Simple command-line interface
- Easy integration into other Python projects

## Installation

1. Clone this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Command Line

Process a single image:
```bash
python bg_remover.py input.jpg -o output.png
```

Process all images in a directory:
```bash
python bg_remover.py /path/to/input/directory -o /path/to/output/directory
```

### Python API

```python
from bg_remover import BackgroundRemover

# Initialize with default model (u2net)
remover = BackgroundRemover(model_name="u2net")

# Process single image
remover.remove_background("input.jpg", "output.png")

# Process directory
remover.batch_process("input_dir", "output_dir")
```

## Available Models

- `u2net`: General purpose model (default)
- `u2netp`: Lighter version of u2net
- `u2net_human_seg`: Optimized for human portraits
- `u2net_cloth_seg`: Optimized for clothing items

## License

MIT
