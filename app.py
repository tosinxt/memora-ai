import os
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
                <div id="dropZone" class="dropzone p-12 text-center cursor-pointer">
                    <input type="file" id="fileInput" class="hidden" accept="image/*">
                    <div class="space-y-4">
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
