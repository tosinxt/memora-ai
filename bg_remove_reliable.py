import os
import sys
import time
import argparse
from pathlib import Path
from typing import List, Optional, Tuple
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
from rembg import new_session, remove
from PIL import Image

class BackgroundRemover:
    def __init__(self, model_name: str = "u2net"):
        """Initialize with a specific model and keep it in memory."""
        self.session = new_session(model_name)
        
    def process_image(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        quality: int = 95,
        alpha_matting: bool = True
    ) -> str:
        """Process a single image and return the output path."""
        try:
            if output_path is None:
                output_path = str(Path(input_path).with_stem(f"{Path(input_path).stem}_nobg"))
            
            with Image.open(input_path) as img:
                output_img = remove(
                    img,
                    session=self.session,
                    alpha_matting=alpha_matting,
                    alpha_matting_foreground_threshold=240,
                    alpha_matting_background_threshold=10,
                    alpha_matting_erode_size=10,
                )
                
                # Optimize PNG compression
                output_img.save(
                    output_path,
                    'PNG',
                    optimize=True,
                    compress_level=1,  # Faster compression (0-9, 0 is no compression)
                    quality=quality
                )
                
            return output_path
            
        except Exception as e:
            print(f"Error processing {input_path}: {str(e)}")
            return None

def process_single_file(args: Tuple) -> Optional[str]:
    """Helper function for multiprocessing."""
    remover, input_path, output_path, quality, alpha_matting = args
    return remover.process_image(input_path, output_path, quality, alpha_matting)

def process_directory(
    input_dir: str,
    output_dir: str,
    remover: BackgroundRemover,
    quality: int = 95,
    alpha_matting: bool = True,
    num_workers: int = None
) -> List[str]:
    """Process all images in a directory."""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get all image files
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
    image_files = [f for f in input_dir.glob('*') if f.suffix.lower() in image_extensions]
    
    if not image_files:
        print(f"No image files found in {input_dir}")
        return []
    
    # Prepare arguments for multiprocessing
    tasks = [(remover, str(f), str(output_dir / f.name), quality, alpha_matting) 
             for f in image_files]
    
    # Process images in parallel
    results = []
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(process_single_file, task) for task in tasks]
        
        # Show progress bar
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing images"):
            result = future.result()
            if result:
                results.append(result)
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Remove background from images with optimizations')
    parser.add_argument('input', help='Input image path or directory')
    parser.add_argument('output', nargs='?', help='Output image path or directory (optional)')
    parser.add_argument('-m', '--model', default='u2net', help='Model to use (default: u2net)')
    parser.add_argument('-q', '--quality', type=int, default=95, help='Output quality (1-100, default: 95)')
    parser.add_argument('--no-alpha-matting', action='store_false', dest='alpha_matting', 
                       help='Disable alpha matting (faster but lower quality edges)')
    parser.add_argument('-w', '--workers', type=int, default=None, 
                       help='Number of worker processes (default: number of CPU cores)')
    
    args = parser.parse_args()
    
    # Initialize the remover (model is loaded once and reused)
    start_time = time.time()
    print("Loading model...")
    remover = BackgroundRemover(model_name=args.model)
    print(f"Model loaded in {time.time() - start_time:.2f} seconds")
    
    input_path = Path(args.input)
    
    if input_path.is_file():
        # Process single file
        if args.output:
            output_path = Path(args.output)
            if output_path.is_dir():
                # If output is a directory, use the input filename with _nobg suffix
                output_path = output_path / f"{input_path.stem}_nobg.png"
            else:
                # Ensure the output has .png extension
                output_path = output_path.with_suffix('.png')
        else:
            # Default output path if none provided
            output_path = input_path.with_stem(f"{input_path.stem}_nobg").with_suffix('.png')
        
        # Create parent directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
            
        start_time = time.time()
        result = remover.process_image(
            str(input_path),
            str(output_path),
            quality=args.quality,
            alpha_matting=args.alpha_matting
        )
        if result:
            print(f"Processed in {time.time() - start_time:.2f} seconds")
            print(f"Output saved to: {result}")
            
    elif input_path.is_dir():
        # Process directory
        output_dir = args.output or str(input_path) + "_nobg"
        start_time = time.time()
        
        results = process_directory(
            str(input_path),
            output_dir,
            remover,
            quality=args.quality,
            alpha_matting=args.alpha_matting,
            num_workers=args.workers
        )
        
        if results:
            print(f"\nProcessed {len(results)} images in {time.time() - start_time:.2f} seconds")
            print(f"Average time per image: {(time.time() - start_time) / len(results):.2f} seconds")
            print(f"Output saved to: {output_dir}")
    else:
        print(f"Error: {args.input} does not exist")
        sys.exit(1)

if __name__ == "__main__":
    main()
