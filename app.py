from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from rembg import remove, new_session
from PIL import Image
import io
import base64
import os

app = Flask(__name__, static_folder='.')
CORS(app)

# Initialize AI model (using lightweight model for faster deployment)
print("🔄 Loading AI model...")
session_u2net = new_session('u2net')
print("✅ AI model loaded!")

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/remove-background', methods=['POST'])
def remove_background():
    try:
        print("📸 Received image processing request")
        
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        print(f"📁 Processing file: {file.filename}")
        
        # Read and prepare image
        input_image = Image.open(file.stream)
        print(f"🖼️ Image size: {input_image.size}, Mode: {input_image.mode}")
        
        # Convert to RGB if necessary
        if input_image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', input_image.size, (255, 255, 255))
            if input_image.mode == 'P':
                input_image = input_image.convert('RGBA')
            if input_image.mode in ('RGBA', 'LA'):
                background.paste(input_image, mask=input_image.split()[-1])
            else:
                background.paste(input_image)
            input_image = background
        elif input_image.mode != 'RGB':
            input_image = input_image.convert('RGB')
        
        print("🤖 Running AI background removal...")
        # Remove background using AI
        output_image = remove(
            input_image,
            session=session_u2net,
            alpha_matting=True,
            alpha_matting_foreground_threshold=240,
            alpha_matting_background_threshold=10,
            alpha_matting_erode_size=10
        )
        print("✅ Background removed successfully!")
        
        # Convert to base64 for JSON response
        img_io = io.BytesIO()
        output_image.save(img_io, 'PNG', optimize=True)
        img_io.seek(0)
        img_base64 = base64.b64encode(img_io.getvalue()).decode()
        
        print("📤 Sending result back to client")
        return jsonify({
            'success': True,
            'image': f'data:image/png;base64,{img_base64}'
        })
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'message': 'AI Background Remover is running!'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"🚀 Starting server on port {port}")
    app.run(host='0.0.0.0', port=port)
