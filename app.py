from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from PIL import Image
import io
import base64
import os

app = Flask(__name__, static_folder='.')
CORS(app)

# Import the simpler background remover
try:
    from transparent_background import Remover
    remover = Remover(fast=True, jit=True, device='cpu')
    print("✅ Background remover loaded!")
except Exception as e:
    print(f"⚠️ Error loading remover: {e}")
    remover = None

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/remove-background', methods=['POST'])
def remove_background():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        input_image = Image.open(file.stream).convert('RGB')
        
        # Remove background
        if remover:
            output_image = remover.process(input_image, type='rgba')
        else:
            return jsonify({'error': 'Background remover not initialized'}), 500
        
        # Convert to base64
        img_io = io.BytesIO()
        output_image.save(img_io, 'PNG')
        img_io.seek(0)
        img_base64 = base64.b64encode(img_io.getvalue()).decode()
        
        return jsonify({
            'success': True,
            'image': f'data:image/png;base64,{img_base64}'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
