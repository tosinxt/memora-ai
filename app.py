import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from pathlib import Path
from bg_remove_reliable import BackgroundRemover
import uuid
import time

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESULT_FOLDER'] = 'static/results'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload and result directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULT_FOLDER'], exist_ok=True)

# Initialize the background remover
remover = BackgroundRemover(model_name="u2net")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        # Generate unique filename
        file_ext = Path(file.filename).suffix.lower()
        filename = f"{uuid.uuid4()}{file_ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process the image
        output_filename = f"{uuid.uuid4()}.png"
        output_path = os.path.join(app.config['RESULT_FOLDER'], output_filename)
        
        try:
            start_time = time.time()
            remover.process_image(filepath, output_path, alpha_matting=True)
            processing_time = time.time() - start_time
            
            return jsonify({
                'success': True,
                'result_url': f'/static/results/{output_filename}',
                'processing_time': round(processing_time, 2)
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            # Clean up the uploaded file
            if os.path.exists(filepath):
                os.remove(filepath)

@app.route('/static/results/<filename>')
def serve_result(filename):
    return send_from_directory(app.config['RESULT_FOLDER'], filename)

if __name__ == '__main__':
    # Use waitress as production server
    from waitress import serve
    print("Starting server at http://localhost:5000")
    serve(app, host="0.0.0.0", port=5000)
