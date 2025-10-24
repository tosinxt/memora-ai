import os
from pathlib import Path
from typing import Optional, Union, Tuple

import cv2
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance
from rembg import remove
from rembg.session_factory import new_session


class BackgroundRemover:
    def __init__(self, model_name: str = "u2net"):
        """
        Initialize the BackgroundRemover with a specific model.
        
        Args:
            model_name: Name of the model to use for background removal.
                       Options: 'u2net', 'u2netp', 'u2net_human_seg', etc.
        """
        self.model_name = model_name
        self.session = new_session(model_name)

    def _refine_edges(self, image: Image.Image) -> Image.Image:
        """Refine the edges of the foreground object."""
        # Convert to numpy array for OpenCV processing
        img_array = np.array(image)
        
        # Convert to grayscale and apply threshold
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGBA2GRAY)
        _, mask = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
        
        # Apply morphological operations to clean up the mask
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        # Find contours and create a clean mask
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            # Get the largest contour
            largest_contour = max(contours, key=cv2.contourArea)
            mask = np.zeros_like(mask)
            cv2.drawContours(mask, [largest_contour], 0, 255, -1)
        
        # Apply Gaussian blur to the mask for smoother edges
        mask = cv2.GaussianBlur(mask, (3, 3), 0)
        
        # Convert mask back to alpha channel
        alpha = mask.astype(np.float32) / 255.0
        alpha = np.dstack([alpha] * 4)  # Add alpha channel to all RGBA channels
        
        # Apply the refined alpha to the original image
        result = img_array.astype(np.float32) / 255.0
        result = result * alpha
        result = (result * 255).astype(np.uint8)
        
        return Image.fromarray(result)
    
    def _sharpen_image(self, image: Image.Image, factor: float = 1.5) -> Image.Image:
        """Sharpen the image while preserving transparency."""
        # Split the image into RGB and alpha channels
        r, g, b, a = image.split()
        
        # Convert to RGB for sharpening
        rgb_image = Image.merge('RGB', (r, g, b))
        
        # Apply sharpening
        enhancer = ImageEnhance.Sharpness(rgb_image)
        sharpened_rgb = enhancer.enhance(factor)
        
        # Convert back to RGBA and restore alpha channel
        r, g, b = sharpened_rgb.split()
        return Image.merge('RGBA', (r, g, b, a))
    
    def remove_background(
        self,
        input_path: Union[str, Path, Image.Image],
        output_path: Optional[Union[str, Path]] = None,
        alpha_matting: bool = True,  # Enable alpha matting by default for better edges
        alpha_matting_foreground_threshold: int = 240,
        alpha_matting_background_threshold: int = 10,
        alpha_matting_erode_size: int = 10,
        alpha_matting_shift: float = 0.0,  # Shift parameter for alpha matting
        refine_edges: bool = True,   # Enable edge refinement by default
        sharpen: bool = True,        # Enable sharpening by default
        sharpen_factor: float = 1.5,  # Sharpen intensity (1.0 = no sharpening)
        post_process: bool = True    # Enable post-processing
    ) -> Image.Image:
        """
        Remove background from an image.
        
        Args:
            input_path: Path to input image or PIL Image
            output_path: Path to save the output image (optional)
            alpha_matting: Whether to use alpha matting
            alpha_matting_foreground_threshold: Foreground threshold for alpha matting
            alpha_matting_background_threshold: Background threshold for alpha matting
            alpha_matting_erode_size: Erode size for alpha matting
            
        Returns:
            PIL Image with background removed
        """
        # Load image if input is a path
        if isinstance(input_path, (str, Path)):
            input_img = Image.open(input_path)
        else:
            input_img = input_path

        # Remove background with error handling for alpha matting
        try:
            output_img = remove(
                input_img,
                session=self.session,
                alpha_matting=alpha_matting,
                alpha_matting_foreground_threshold=alpha_matting_foreground_threshold,
                alpha_matting_background_threshold=alpha_matting_background_threshold,
                alpha_matting_erode_size=alpha_matting_erode_size,
                alpha_matting_shift=alpha_matting_shift,
            )
        except Exception as e:
            print(f"Warning during alpha matting: {str(e)}")
            print("Retrying with alpha matting disabled...")
            output_img = remove(
                input_img,
                session=self.session,
                alpha_matting=False
            )
        
        # Apply post-processing if enabled
        if post_process:
            # Apply edge refinement if enabled
            if refine_edges:
                output_img = self._refine_edges(output_img)
            
            # Apply sharpening if enabled
            if sharpen and sharpen_factor > 1.0:
                output_img = self._sharpen_image(output_img, factor=sharpen_factor)

        # Save output if path is provided
        if output_path is not None:
            output_img.save(output_path, 'PNG', compress_level=0)  # No compression for maximum quality
            print(f"Image with background removed saved to: {output_path}")

        return output_img

    def batch_process(
        self,
        input_dir: Union[str, Path],
        output_dir: Union[str, Path],
        file_extensions: tuple = ('.jpg', '.jpeg', '.png'),
        **kwargs
    ) -> None:
        """
        Process all images in a directory.
        
        Args:
            input_dir: Directory containing input images
            output_dir: Directory to save processed images
            file_extensions: Tuple of file extensions to process
            **kwargs: Additional arguments to pass to remove_background
        """
        input_dir = Path(input_dir)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        processed = 0
        for ext in file_extensions:
            for img_path in input_dir.glob(f'*{ext}'):
                output_path = output_dir / f"{img_path.stem}_nobg.png"
                try:
                    self.remove_background(str(img_path), str(output_path), **kwargs)
                    processed += 1
                except Exception as e:
                    print(f"Error processing {img_path}: {e}")
        
        print(f"\nProcessing complete! {processed} images were processed.")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Remove background from images')
    parser.add_argument('input', help='Input image path or directory')
    parser.add_argument('-o', '--output', help='Output image path or directory')
    parser.add_argument('--model', default='u2net', help='Model to use (default: u2net)')
    # Alpha matting arguments
    parser.add_argument('--alpha-matting', action='store_true', default=True, help='Use alpha matting (enabled by default for better edges)')
    parser.add_argument('--no-alpha-matting', dest='alpha_matting', action='store_false', help='Disable alpha matting')
    parser.add_argument('--foreground-threshold', type=int, default=240, help='Foreground threshold for alpha matting (0-255, default: 240)')
    parser.add_argument('--background-threshold', type=int, default=10, help='Background threshold for alpha matting (0-255, default: 10)')
    parser.add_argument('--erode-size', type=int, default=10, help='Erode size for alpha matting (default: 10)')
    parser.add_argument('--matting-shift', type=float, default=0.0, help='Shift parameter for alpha matting (default: 0.0)')
    
    # Post-processing arguments
    parser.add_argument('--sharpen', type=float, default=1.5, help='Sharpen factor (1.0 = no sharpening, default: 1.5)')
    parser.add_argument('--no-refine', dest='refine_edges', action='store_false', default=True, help='Disable edge refinement')
    parser.add_argument('--no-post-process', dest='post_process', action='store_false', default=True, help='Disable all post-processing')
    
    args = parser.parse_args()
    
    remover = BackgroundRemover(model_name=args.model)
    
    if os.path.isfile(args.input):
        # Process single file
        output_path = args.output or f"{os.path.splitext(args.input)[0]}_nobg.png"
        remover.remove_background(
            args.input, 
            output_path, 
            alpha_matting=args.alpha_matting,
            alpha_matting_foreground_threshold=args.foreground_threshold,
            alpha_matting_background_threshold=args.background_threshold,
            alpha_matting_erode_size=args.erode_size,
            alpha_matting_shift=args.matting_shift,
            refine_edges=args.refine_edges,
            sharpen=args.sharpen > 1.0,
            sharpen_factor=args.sharpen,
            post_process=args.post_process
        )
    else:
        # Process directory
        output_dir = args.output or f"{args.input}_nobg"
        remover.batch_process(
            args.input, 
            output_dir, 
            alpha_matting=args.alpha_matting,
            alpha_matting_foreground_threshold=args.foreground_threshold,
            alpha_matting_background_threshold=args.background_threshold,
            alpha_matting_erode_size=args.erode_size,
            alpha_matting_shift=args.matting_shift,
            refine_edges=args.refine_edges,
            sharpen=args.sharpen > 1.0,
            sharpen_factor=args.sharpen,
            post_process=args.post_process
        )


if __name__ == "__main__":
    main()
