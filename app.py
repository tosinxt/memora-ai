import os
<<<<<<< HEAD
import subprocess
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path
import uvicorn
=======
import uuid
import logging
import traceback
from fastapi import FastAPI, UploadFile, File, HTTPException, Request, status
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from typing import Optional, Dict, Any
import uvicorn
from rembg import new_session, remove, __version__ as rembg_version
from PIL import Image, ImageFile
import io
import sys
>>>>>>> 8f5c616 (lets go!)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Allow loading of truncated images
ImageFile.LOAD_TRUNCATED_IMAGES = True

# Initialize FastAPI app
app = FastAPI(
    title="Background Remover",
    description="Remove background from images using AI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None
)

# Global error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred. Please try again later."}
    )

# Create necessary directories
UPLOAD_FOLDER = "uploads"
<<<<<<< HEAD
Path(UPLOAD_FOLDER).mkdir(exist_ok=True)

# No need for static files in this simplified version

def remove_background(image_path: str, output_path: str) -> bool:
    """Remove background using rembg CLI"""
    try:
        result = subprocess.run(
            ["rembg", "i", image_path, output_path],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"Error in remove_background: {str(e)}")
        return False
=======
OUTPUT_FOLDER = "static/results"
Path(UPLOAD_FOLDER).mkdir(exist_ok=True)
Path(OUTPUT_FOLDER).mkdir(exist_ok=True, parents=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize model (load once at startup)
try:
    logger.info(f"Initializing U2Net model (rembg v{rembg_version})...")
    model = new_session("u2net")
    logger.info("Model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load model: {str(e)}")
    logger.error(traceback.format_exc())
    raise RuntimeError("Failed to initialize the AI model. Please check the logs for details.")

def remove_background(image_data: bytes, output_path: Optional[str] = None) -> bytes:
    """Remove background from image and return bytes"""
    try:
        img = Image.open(io.BytesIO(image_data))
        output = remove(img, session=model)
        
        if output_path:
            output.save(output_path, 'PNG', optimize=True)
        
        img_byte_arr = io.BytesIO()
        output.save(img_byte_arr, format='PNG')
        return img_byte_arr.getvalue()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")
>>>>>>> 8f5c616 (lets go!)

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "background-remover",
        "version": "1.0.0"
    }

@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the main application page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Background Remover</title>
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        <style>
            .dropzone {
                border: 2px dashed #4a5568;
                border-radius: 0.5rem;
                transition: all 0.2s;
            }
            .dropzone:hover {
                border-color: #4299e1;
                background-color: #f7fafc;
            }
        </style>
    </head>
    <body class="bg-gray-100 min-h-screen p-8">
        <div class="max-w-4xl mx-auto">
            <h1 class="text-4xl font-bold text-center mb-8 text-gray-800">Background Remover</h1>
            
            <div class="bg-white rounded-lg shadow-lg p-6 mb-8">
<<<<<<< HEAD
                <form action="/remove-bg" method="post" enctype="multipart/form-data" class="space-y-4">
                    <div class="dropzone p-12 text-center cursor-pointer">
                        <input type="file" name="file" id="fileInput" class="hidden" accept="image/*" required>
                        <div class="space-y-4">
=======
                <div id="dropZone" class="dropzone p-12 text-center cursor-pointer">
                    <input type="file" id="fileInput" class="hidden" accept="image/*">
                    <div class="space-y-4">
>>>>>>> 8f5c616 (lets go!)
                        <svg class="mx-auto h-16 w-16 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                        </svg>
                        <p class="text-lg text-gray-600">Drag & drop an image here, or click to select</p>
                        <p class="text-sm text-gray-500">Supports JPG, PNG, WEBP (Max 10MB)</p>
                    </div>
                </div>
                
                <div id="preview" class="mt-6 hidden">
                    <div class="flex flex-col md:flex-row gap-8">
                        <div class="flex-1">
                            <h3 class="text-lg font-medium text-gray-700 mb-2">Original</h3>
                            <div class="bg-gray-100 rounded-lg p-2">
                                <img id="originalPreview" class="max-w-full h-auto mx-auto" src="" alt="Original">
                            </div>
                        </div>
                        <div class="flex-1">
                            <h3 class="text-lg font-medium text-gray-700 mb-2">Result</h3>
                            <div class="bg-gray-100 rounded-lg p-2">
                                <img id="resultPreview" class="max-w-full h-auto mx-auto" src="" alt="Result">
                            </div>
                        </div>
                    </div>
                    
                    <div id="downloadSection" class="mt-6 text-center hidden">
                        <a id="downloadBtn" href="#" class="inline-flex items-center px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path>
                            </svg>
                            Download Image
                        </a>
<<<<<<< HEAD
            
            <div id="result" class="mt-8 hidden">
                <h2 class="text-2xl font-semibold mb-4">Result</h2>
                <div class="bg-gray-100 p-4 rounded-lg">
                    <img id="resultImage" src="" alt="Result" class="max-w-full h-auto rounded">
                </div>
                <div class="mt-4 flex justify-end">
                    <a id="downloadBtn" href="#" class="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-lg transition duration-200">
                        Download Image
                    </a>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Simple file input handling
        const fileInput = document.getElementById('fileInput');
        const dropZone = document.querySelector('.dropzone');
        const result = document.getElementById('result');
        const resultImage = document.getElementById('resultImage');
        const downloadBtn = document.getElementById('downloadBtn');
        
        // Handle file selection
        fileInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file && file.type.match('image.*')) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    resultImage.src = e.target.result;
                    result.classList.remove('hidden');
                    
                    // Update download link
                    const url = URL.createObjectURL(file);
                    downloadBtn.href = url;
                    downloadBtn.download = 'nobg_' + file.name;
                    
                    // Scroll to result
                    result.scrollIntoView({ behavior: 'smooth' });
                }
                reader.readAsDataURL(file);
            }
        });

        // Handle form submission
        const form = document.querySelector('form');
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(form);
            const submitBtn = form.querySelector('button[type="submit"]');
            const originalBtnText = submitBtn.textContent;
            
            try {
                submitBtn.disabled = true;
                submitBtn.innerHTML = 'Processing...';
                
                const response = await fetch('/remove-bg', {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) {
                    const error = await response.text();
                    throw new Error(error || 'Failed to process image');
                }
                
                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                
                // Show result
                resultImage.src = url;
                downloadBtn.href = url;
                downloadBtn.download = 'nobg_' + fileInput.files[0].name;
                result.classList.remove('hidden');
                
                // Scroll to result
                result.scrollIntoView({ behavior: 'smooth' });
                
            } catch (error) {
                alert('Error: ' + error.message);
                console.error('Error:', error);
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = originalBtnText;
            }
        });
    </script>
</body>
</html>
=======
                    </div>
                </div>
                
                <div id="loading" class="mt-6 text-center hidden">
                    <div class="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-600"></div>
                    <p class="mt-2 text-gray-600">Removing background...</p>
                </div>
                
                <div id="error" class="mt-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded hidden">
                    <p id="errorMessage"></p>
                </div>
            </div>
            
            <div class="text-center text-sm text-gray-500">
                <p>Background Remover - Powered by U²-Net & FastAPI</p>
            </div>
        </div>
        
        <script>
            const dropZone = document.getElementById('dropZone');
            const fileInput = document.getElementById('fileInput');
            const originalPreview = document.getElementById('originalPreview');
            const resultPreview = document.getElementById('resultPreview');
            const previewSection = document.getElementById('preview');
            const downloadSection = document.getElementById('downloadSection');
            const downloadBtn = document.getElementById('downloadBtn');
            const loading = document.getElementById('loading');
            const errorDiv = document.getElementById('error');
            const errorMessage = document.getElementById('errorMessage');
            
            let currentResultUrl = '';
            
            // Handle drag and drop
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                dropZone.addEventListener(eventName, preventDefaults, false);
            });
            
            function preventDefaults(e) {
                e.preventDefault();
                e.stopPropagation();
            }
            
            ['dragenter', 'dragover'].forEach(eventName => {
                dropZone.addEventListener(eventName, highlight, false);
            });
            
            ['dragleave', 'drop'].forEach(eventName => {
                dropZone.addEventListener(eventName, unhighlight, false);
            });
            
            function highlight() {
                dropZone.classList.add('border-blue-500', 'bg-blue-50');
            }
            
            function unhighlight() {
                dropZone.classList.remove('border-blue-500', 'bg-blue-50');
            }
            
            // Handle file selection
            dropZone.addEventListener('click', () => fileInput.click());
            
            fileInput.addEventListener('change', handleFiles);
            dropZone.addEventListener('drop', handleDrop);
            
            function handleDrop(e) {
                const dt = e.dataTransfer;
                const files = dt.files;
                handleFiles({ target: { files } });
            }
            
            function handleFiles(e) {
                const files = e.target.files;
                if (files.length === 0) return;
                
                const file = files[0];
                if (!file.type.match('image.*')) {
                    showError('Please select an image file');
                    return;
                }
                
                if (file.size > 10 * 1024 * 1024) { // 10MB limit
                    showError('File size should be less than 10MB');
                    return;
                }
                
                const reader = new FileReader();
                reader.onload = function(e) {
                    originalPreview.src = e.target.result;
                    processImage(file);
                };
                reader.readAsDataURL(file);
            }
            
            async function processImage(file) {
                try {
                    // Show loading state
                    previewSection.classList.add('hidden');
                    downloadSection.classList.add('hidden');
                    errorDiv.classList.add('hidden');
                    loading.classList.remove('hidden');
                    
                    const formData = new FormData();
                    formData.append('file', file);
                    
                    const response = await fetch('/remove-bg', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (!response.ok) {
                        const error = await response.json();
                        throw new Error(error.detail || 'Failed to process image');
                    }
                    
                    const blob = await response.blob();
                    const url = URL.createObjectURL(blob);
                    
                    // Clean up previous URL if exists
                    if (currentResultUrl) {
                        URL.revokeObjectURL(currentResultUrl);
                    }
                    currentResultUrl = url;
                    
                    // Update UI
                    resultPreview.src = url;
                    downloadBtn.href = url;
                    downloadBtn.download = `nobg_${file.name.replace(/\.[^/.]+$/, '')}.png`;
                    
                    // Show results
                    previewSection.classList.remove('hidden');
                    downloadSection.classList.remove('hidden');
                    loading.classList.add('hidden');
                    
                } catch (error) {
                    console.error('Error:', error);
                    showError(error.message || 'An error occurred while processing the image');
                    loading.classList.add('hidden');
                }
            }
            
            function showError(message) {
                errorMessage.textContent = message;
                errorDiv.classList.remove('hidden');
            }
        </script>
    </body>
    </html>
>>>>>>> 8f5c616 (lets go!)
    """

@app.post("/remove-bg")
async def remove_bg(file: UploadFile = File(...)):
    """Remove background from uploaded image"""
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="File must be an image (JPEG, PNG, etc.)"
            )
            
        # Read file with size limit (10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        contents = await file.read()
        if len(contents) > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size is {max_size/1024/1024}MB"
            )
        
        logger.info(f"Processing image: {file.filename} ({len(contents)/1024:.1f}KB)")
        
<<<<<<< HEAD
        # Save uploaded file
        input_path = os.path.join(UPLOAD_FOLDER, file.filename)
        output_path = os.path.join(UPLOAD_FOLDER, f"nobg_{file.filename}")
        
        with open(input_path, "wb") as f:
            f.write(contents)
        
        # Process image using rembg
        success = remove_background(input_path, output_path)
        
        if not success or not os.path.exists(output_path):
            raise HTTPException(
                status_code=500,
                detail="Failed to process image"
            )
        
        # Return the processed image
        return FileResponse(
            output_path,
            media_type="image/png",
            filename=f"nobg_{file.filename}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}"
        )
    finally:
        # Clean up temporary files
        if 'input_path' in locals() and os.path.exists(input_path):
            os.remove(input_path)
        # Note: output_path is returned as a FileResponse which handles its own cleanup

if __name__ == "__main__":
    # For development
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
=======
        # Process image
        try:
            result = remove_background(contents)
            logger.info(f"Successfully processed image: {file.filename}")
            # Create a response with the image data
            return Response(
                content=result,
                media_type="image/png",
                headers={"Content-Disposition": f"inline; filename=nobg_{file.filename}"}
            )
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process image: {str(e)}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing your request"
        )

if __name__ == "__main__":
    # For development
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
>>>>>>> 8f5c616 (lets go!)
