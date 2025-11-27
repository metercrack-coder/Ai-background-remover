from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from rembg import remove, new_session
from PIL import Image
import io
import base64
import os

app = Flask(__name__, static_folder='.')
CORS(app)

# Initialize AI models
sessions = {
    'u2net': new_session('u2net'),
    'u2netp': new_session('u2netp'),
    'u2net_human_seg': new_session('u2net_human_seg'),
}

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/remove-background', methods=['POST'])
def remove_background():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        model = request.form.get('model', 'u2net')
        
        if model not in sessions:
            model = 'u2net'
        
        input_image = Image.open(file.stream)
        
        # Convert to RGB if necessary
        if input_image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', input_image.size, (255, 255, 255))
            if input_image.mode == 'P':
                input_image = input_image.convert('RGBA')
            background.paste(input_image, mask=input_image.split()[-1] if input_image.mode in ('RGBA', 'LA') else None)
            input_image = background
        elif input_image.mode != 'RGB':
            input_image = input_image.convert('RGB')
        
        # Remove background
        output_image = remove(
            input_image,
            session=sessions[model],
            alpha_matting=True,
            alpha_matting_foreground_threshold=240,
            alpha_matting_background_threshold=10,
            alpha_matting_erode_size=10
        )
        
        # Convert to base64
        img_io = io.BytesIO()
        output_image.save(img_io, 'PNG', optimize=True)
        img_io.seek(0)
        img_base64 = base64.b64encode(img_io.getvalue()).decode()
        
        return jsonify({
            'success': True,
            'image': f'data:image/png;base64,{img_base64}',
            'model_used': model
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)