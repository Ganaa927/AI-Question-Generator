# Install required packages (run this in a separate cell in Colab)
# !pip install flask-ngrok google-generativeai --quiet

import json
import threading
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import google.generativeai as genai


def create_app():
    """Create and configure the Flask application"""


app = Flask(__name__)
    CORS(app)  # Enable CORS for all routes

    # Configure Gemini API
    # You need to set your API key - get it from https://makersuite.google.com/app/apikey
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'YOUR_API_KEY_HERE')

    if GEMINI_API_KEY and GEMINI_API_KEY != 'YOUR_API_KEY_HERE':
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-pro')
    else:
        model = None
        print("⚠️  WARNING: GEMINI_API_KEY not set! Please set your API key.")
        print("   Get your API key from: https://makersuite.google.com/app/apikey")
        print("   Set it as: os.environ['GEMINI_API_KEY'] = 'your-key-here'")

    @app.route('/')
    def index():
        """Serve the main HTML page"""
        try:
            with open('ai_question_generator.html', 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return jsonify({"error": "Frontend HTML file not found"}), 404


@app.route('/generate', methods=['POST'])
def generate():
        """Generate similar questions using Gemini AI"""
        try:
            data = request.get_json()
            prompt = data.get("prompt", "").strip()
            json_data = data.get("data", {})

            if not prompt:
                return jsonify({"error": "Prompt is required"}), 400

            if not json_data:
                return jsonify({"error": "JSON data is required"}), 400

            # Check if Gemini model is available
            if not model:
                return jsonify({
                    "error": "Gemini API not configured. Please set GEMINI_API_KEY environment variable.",
                    "setup_instructions": {
                        "step1": "Get API key from https://makersuite.google.com/app/apikey",
                        "step2": "Set environment variable: os.environ['GEMINI_API_KEY'] = 'your-key-here'",
                        "step3": "Restart the Flask server"
                    }
                }), 500

            # Optimize prompt for faster generation - shorter and more direct
            sample_structure = str(json_data)[
                :500] + "..." if len(str(json_data)) > 500 else str(json_data)

            gemini_prompt = f"""Generate similar questions following this JSON structure:

INPUT: {sample_structure}

TASK: {prompt}

RULES:
- Same JSON format
- Same question type
- Similar difficulty
- Valid JSON only
- No explanations

OUTPUT:"""

            try:
                # Generate content using Gemini with optimized settings
                response = model.generate_content(
                    gemini_prompt,
                    generation_config={
                        'temperature': 0.7,  # Lower temperature for more focused responses
                        'max_output_tokens': 2048,  # Limit output length
                        'top_p': 0.8,
                        'top_k': 40
                    }
                )
                generated_text = response.text.strip()

                # Try to extract JSON from the response
                # Sometimes Gemini wraps JSON in code blocks
                if '```json' in generated_text:
                    start = generated_text.find('```json') + 7
                    end = generated_text.find('```', start)
                    generated_text = generated_text[start:end].strip()
                elif '```' in generated_text:
                    start = generated_text.find('```') + 3
                    end = generated_text.find('```', start)
                    generated_text = generated_text[start:end].strip()

                # Parse the generated JSON
                try:
                    generated_questions = json.loads(generated_text)
                except json.JSONDecodeError:
                    # If JSON parsing fails, try to clean the text
                    generated_text = generated_text.replace(
                        '\n', '').replace('\\', '')
                    generated_questions = json.loads(generated_text)

                return jsonify({
                    "success": True,
                    "generated_questions": generated_questions,
                    "prompt_used": prompt,
                    "input_structure": "analyzed"
                })

            except json.JSONDecodeError as e:
                return jsonify({
                    "error": f"Failed to parse generated JSON: {str(e)}",
                    "raw_response": generated_text[:500] + "..." if len(generated_text) > 500 else generated_text
                }), 500

            except Exception as e:
                return jsonify({
                    "error": f"Gemini API error: {str(e)}",
                    "troubleshooting": [
                        "Check your API key is valid",
                        "Ensure you have quota remaining",
                        "Try with a simpler prompt",
                        "Check your internet connection"
                    ]
                }), 500

        except Exception as e:
            return jsonify({
                "error": f"Server error: {str(e)}",
                "type": "server_error"
            }), 500

    @app.route('/generate-fast', methods=['POST'])
    def generate_fast():
        """Fast generation with smaller prompts and optimizations"""
        # Import debug logger
        try:
            from debug_logger import log_debug
        except ImportError:
            def log_debug(msg):
                print(f"🔧 DEBUG: {msg}", flush=True)

        try:
            log_debug("Fast generation started")
            import sys

            data = request.get_json()
            print(
                f"🔧 DEBUG: Received data keys: {list(data.keys()) if data else 'None'}", flush=True)
            sys.stdout.flush()

            prompt = data.get("prompt", "").strip()
            json_data = data.get("data", {})

            print(f"🔧 DEBUG: Prompt length: {len(prompt)}", flush=True)
            print(f"🔧 DEBUG: JSON data type: {type(json_data)}", flush=True)
            sys.stdout.flush()

            if not prompt or not json_data:
                print("🔧 DEBUG: Missing prompt or data", flush=True)
                sys.stdout.flush()
                return jsonify({"error": "Prompt and data required"}), 400

            if not model:
                print("🔧 DEBUG: Gemini model not configured", flush=True)
                sys.stdout.flush()
                return jsonify({"error": "Gemini API not configured"}), 500

            # For faster processing, extract just the structure
            try:
                print("🔧 DEBUG: Extracting sample structure...", flush=True)
                sys.stdout.flush()

                if isinstance(json_data, dict) and 'questions' in json_data:
                    sample_q = json_data['questions'][0] if json_data['questions'] else json_data
                elif isinstance(json_data, list) and json_data:
                    sample_q = json_data[0]
                else:
                    sample_q = json_data

                print(
                    f"🔧 DEBUG: Sample structure type: {type(sample_q)}", flush=True)
                sys.stdout.flush()

                # Ultra-short prompt for speed
                sample_json = json.dumps(sample_q, indent=0)[:200]
                fast_prompt = f"Generate {prompt}. Use this format: {sample_json}... JSON only:"
                print(
                    f"🔧 DEBUG: Prompt created, length: {len(fast_prompt)}", flush=True)
                sys.stdout.flush()

            except Exception as extract_error:
                print(
                    f"🔧 DEBUG: Error extracting structure: {extract_error}", flush=True)
                sys.stdout.flush()
                return jsonify({"error": f"Failed to extract JSON structure: {str(extract_error)}"}), 500

            try:
                print("🔧 DEBUG: Calling Gemini API...", flush=True)
                sys.stdout.flush()

                response = model.generate_content(
                    fast_prompt,
                    generation_config={
                        'temperature': 0.5,
                        'max_output_tokens': 1024,  # Smaller limit for speed
                        'top_p': 0.9,
                        'top_k': 20
                    }
                )

                generated_text = response.text.strip()
                print(
                    f"🔧 DEBUG: Generated text length: {len(generated_text)}", flush=True)
                print(
                    f"🔧 DEBUG: First 100 chars: {generated_text[:100]}", flush=True)
                sys.stdout.flush()

                # Quick JSON extraction
                if '```' in generated_text:
                    print("🔧 DEBUG: Found code blocks, extracting JSON...", flush=True)
                    sys.stdout.flush()
                    start = generated_text.find('{')
                    end = generated_text.rfind('}') + 1
                    if start >= 0 and end > start:
                        generated_text = generated_text[start:end]
                        print(
                            f"🔧 DEBUG: Extracted JSON length: {len(generated_text)}", flush=True)
                        sys.stdout.flush()

                print("🔧 DEBUG: Parsing JSON...", flush=True)
                sys.stdout.flush()
                generated_questions = json.loads(generated_text)
                print("🔧 DEBUG: JSON parsed successfully!", flush=True)
                sys.stdout.flush()

                return jsonify({
                    "success": True,
                    "generated_questions": generated_questions,
                    "mode": "fast"
                })

            except Exception as e:
                print(f"🔧 DEBUG: Fast generation exception: {e}", flush=True)
                print(f"🔧 DEBUG: Exception type: {type(e)}", flush=True)
                import traceback
                print(
                    f"🔧 DEBUG: Full traceback:\n{traceback.format_exc()}", flush=True)
                sys.stdout.flush()
                return jsonify({"error": f"Fast generation failed: {str(e)}"}), 500

        except Exception as e:
            print(f"🔧 DEBUG: Server error: {e}", flush=True)
            print(f"🔧 DEBUG: Exception type: {type(e)}", flush=True)
            import traceback
            print(
                f"🔧 DEBUG: Full traceback:\n{traceback.format_exc()}", flush=True)
            sys.stdout.flush()
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route('/health', methods=['GET'])
    def health():
        """Health check endpoint"""
        return jsonify({
            "status": "running",
            "gemini_configured": model is not None,
            "gemini_model": "gemini-2.5-pro" if model else None,
            "api_key_set": bool(os.getenv('GEMINI_API_KEY') and os.getenv('GEMINI_API_KEY') != 'YOUR_API_KEY_HERE'),
            "message": "AI Question Generator Backend is running"
        })

    @app.route('/debug', methods=['POST'])
    def debug_endpoint():
        """Debug endpoint to test data processing"""
        try:
    data = request.get_json()
            return jsonify({
                "received_data": {
                    "keys": list(data.keys()) if data else None,
                    "prompt_length": len(data.get("prompt", "")) if data else 0,
                    "data_type": str(type(data.get("data", {}))) if data else None,
                    "data_size": len(str(data.get("data", {}))) if data else 0
                },
                "model_status": {
                    "configured": model is not None,
                    "api_key_set": bool(GEMINI_API_KEY and GEMINI_API_KEY != 'YOUR_API_KEY_HERE')
                },
                "status": "debug_ok"
            })
        except Exception as e:
            return jsonify({
                "debug_error": str(e),
                "error_type": str(type(e))
            }), 500

    return app


def run_flask_app():
    """Run the Flask app with ngrok in a separate thread"""
    app = create_app()

    # Try different ngrok approaches
    print("🚀 Starting Flask server...")
    print("📁 Serving frontend at root URL")
    print("🤖 Gemini AI integration ready")

    # Method 1: Try pyngrok (more reliable)
    try:
        from pyngrok import ngrok
        import time

        print("🔗 Attempting to create ngrok tunnel with pyngrok...")

        # Start Flask in background
        import threading

        def run_flask():
            app.run(host='127.0.0.1', port=5000,
                    debug=False, use_reloader=False)

        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()

        # Wait for Flask to start
        time.sleep(2)

        # Create ngrok tunnel
        public_url = ngrok.connect(5000)
        print(f"✅ ngrok tunnel created: {public_url}")
        print(f"🌐 Access your web app at: {public_url}")

        # Keep the tunnel alive
        try:
            ngrok_process = ngrok.get_ngrok_process()
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("🛑 Stopping ngrok tunnel...")
            ngrok.disconnect(public_url)

    except ImportError:
        print("📦 pyngrok not found, trying flask-ngrok...")

        # Method 2: Try flask-ngrok
        try:
            from flask_ngrok import run_with_ngrok
            run_with_ngrok(app)
            print("🔗 Using flask-ngrok tunnel")
            app.run()

        except ImportError:
            print("📦 Installing pyngrok for better ngrok support...")
            import subprocess
            subprocess.check_call(['pip', 'install', 'pyngrok', '--quiet'])
            print("✅ Installation complete. Please restart the server.")

        except Exception as ngrok_error:
            print(f"⚠️  flask-ngrok failed: {ngrok_error}")
            run_local_fallback(app)

    except Exception as e:
        print(f"⚠️  pyngrok failed: {e}")
        run_local_fallback(app)


def run_local_fallback(app):
    """Fallback to local server if ngrok fails"""
    print("🔄 Starting local server as fallback...")
    print("⚠️  Note: This will only be accessible within Colab")
    print("💡 For external access, install ngrok: !pip install pyngrok --quiet")

    try:
        # Try to use Colab's built-in port forwarding
        try:
            from google.colab.output import eval_js
            print("🔗 Attempting to use Colab port forwarding...")
            port_url = eval_js("google.colab.kernel.proxyPort(5000)")
            print(f"🌐 Access your app at: {port_url}")
        except:
            print("🔗 Local access: http://127.0.0.1:5000")

        app.run(host='127.0.0.1', port=5000, debug=False)

    except Exception as fallback_error:
        print(f"❌ All methods failed: {fallback_error}")
        print("🔧 Try restarting the Colab runtime and running again")


def setup_api_key():
    """Helper function to set up Gemini API key"""
    print("🔑 Setting up Gemini API Key...")
    print("1. Go to: https://makersuite.google.com/app/apikey")
    print("2. Create a new API key")
    print("3. Run: os.environ['GEMINI_API_KEY'] = 'your-api-key-here'")
    print("4. Then restart this server")


# Only run if this script is executed directly
if __name__ == "__main__":
    # Check if API key is set
    if not os.getenv('GEMINI_API_KEY') or os.getenv('GEMINI_API_KEY') == 'YOUR_API_KEY_HERE':
        setup_api_key()

    # Run in a separate thread to avoid Colab conflicts
    flask_thread = threading.Thread(target=run_flask_app, daemon=True)
    flask_thread.start()

    print("🌟 AI Question Generator Server starting...")
    print("📱 Access the web interface via the ngrok URL")
    print("⚡ The server will generate similar questions using Google Gemini AI")

    # Keep the main thread alive
    try:
        flask_thread.join()
    except KeyboardInterrupt:
        print("🛑 Server stopped by user")
