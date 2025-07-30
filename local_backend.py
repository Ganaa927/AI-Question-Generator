#!/usr/bin/env python3
"""
AI Question Generator - Local Development Backend
Optimized for running in IDE with proper error handling and debugging
"""

import json
import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

# Set up logging for local development
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def create_app():
    """Create and configure the Flask application for local development"""
    app = Flask(__name__)
    CORS(app)

    logger.info("🚀 Starting AI Question Generator (Local Mode)")

    # Configure Gemini API
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

    if not GEMINI_API_KEY or GEMINI_API_KEY == 'YOUR_API_KEY_HERE':
        logger.error("❌ GEMINI_API_KEY not set!")
        logger.info(
            "Set it with: export GEMINI_API_KEY='your-key' (Linux/Mac) or $env:GEMINI_API_KEY='your-key' (Windows)")
        model = None
    else:
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            # Use the standard model that's more reliable
            model = genai.GenerativeModel('gemini-2.5-pro')
            logger.info("✅ Gemini model configured successfully")
        except Exception as e:
            logger.error(f"❌ Error configuring Gemini: {e}")
            model = None

    @app.route('/')
    def index():
        """Serve the main HTML page"""
        try:
            with open('ai_question_generator.html', 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logger.error("HTML file not found")
            return jsonify({"error": "Frontend HTML file not found"}), 404

    @app.route('/health', methods=['GET'])
    def health():
        """Health check endpoint"""
        logger.info("Health check requested")
        return jsonify({
            "status": "running",
            "gemini_configured": model is not None,
            "api_key_set": bool(GEMINI_API_KEY),
            "mode": "local_development"
        })

    @app.route('/generate-fast', methods=['POST'])
    def generate_fast():
        """Fast generation with detailed error handling"""
        logger.info("=== FAST GENERATION REQUEST START ===")

        try:
            # Step 1: Get request data
            logger.debug("Step 1: Getting request data")
            data = request.get_json()

            if not data:
                logger.error("No JSON data received")
                return jsonify({"error": "No JSON data received"}), 400

            logger.debug(f"Received data keys: {list(data.keys())}")

            # Step 2: Extract parameters
            language = data.get("language", "English").strip()
            topic = data.get("topic", "").strip()
            num_questions = data.get("num_questions", 10)
            json_data = data.get("data", {})

            logger.debug(f"Language: {language}")
            logger.debug(f"Topic: {topic}")
            logger.debug(f"Number of questions: {num_questions}")
            logger.debug(f"JSON data type: {type(json_data)}")

            # Step 3: Validate input
            if not topic:
                logger.error("Empty topic received")
                return jsonify({"error": "Topic is required"}), 400

            if not isinstance(num_questions, int) or num_questions < 1 or num_questions > 20:
                logger.error(f"Invalid number of questions: {num_questions}")
                return jsonify({"error": "Number of questions must be between 1 and 20"}), 400

            if not json_data:
                logger.error("Empty JSON data received")
                return jsonify({"error": "JSON data is required"}), 400

            if not model:
                logger.error("Gemini model not configured")
                return jsonify({
                    "error": "Gemini API not configured",
                    "details": "Check your API key"
                }), 500

            logger.info("✅ Input validation passed")

            # Step 4: Extract sample structure
            logger.debug("Step 4: Extracting sample structure")
            try:
                if isinstance(json_data, dict) and 'questions' in json_data:
                    if json_data['questions'] and len(json_data['questions']) > 0:
                        sample_q = json_data['questions'][0]
                        logger.debug(
                            "Using first question from questions array")
                    else:
                        sample_q = {"text": "Sample question", "options": [
                            "A", "B", "C", "D"], "correct": 0}
                        logger.debug(
                            "Empty questions array, using default structure")
                elif isinstance(json_data, list) and json_data:
                    # If it's a list, check if the first item has a questions array
                    first_item = json_data[0]
                    if isinstance(first_item, dict) and 'questions' in first_item and first_item['questions']:
                        sample_q = first_item['questions'][0]
                        logger.debug(
                            "Using first question from first item's questions array")
                    else:
                        sample_q = first_item
                        logger.debug("Using first item from list as sample")
                elif isinstance(json_data, dict):
                    sample_q = json_data
                    logger.debug("Using entire dict as sample structure")
                else:
                    # Fallback for other types
                    sample_q = {"text": "Sample question",
                                "options": ["A", "B", "C", "D"], "correct": 0}
                    logger.debug("Using default sample structure")

                logger.debug(f"Sample structure type: {type(sample_q)}")
                logger.debug(
                    f"Sample structure keys: {list(sample_q.keys()) if isinstance(sample_q, dict) else 'Not a dict'}")

            except Exception as e:
                logger.error(f"Error extracting structure: {e}")
                return jsonify({"error": f"Failed to extract JSON structure: {str(e)}"}), 500

                # Step 5: Create prompt
            logger.debug("Step 5: Creating Gemini prompt")
            try:
                # Create the educational prompt for language learning
                base_ex = json_data  # Use the uploaded JSON as the base example

                # Handle different JSON structures (list vs dict)
                if isinstance(base_ex, list):
                    # If it's a list, use the first item or create a simple structure
                    if base_ex:
                        base_ex_str = json.dumps(
                            base_ex[0], indent=0, ensure_ascii=False)
                    else:
                        base_ex_str = json.dumps(
                            {"example": "structure"}, indent=0, ensure_ascii=False)
                elif isinstance(base_ex, dict):
                    # Create a more concise prompt to avoid truncation
                    base_ex_str = json.dumps(
                        base_ex, indent=0, ensure_ascii=False)
                    if len(base_ex_str) > 2000:  # Limit example size
                        # Extract just the structure with first question as example
                        structure_example = {
                            "data": base_ex.get("data", {}),
                            "questions": base_ex.get("questions", [{}])[:1] if base_ex.get("questions") else [{}]
                        }
                        base_ex_str = json.dumps(
                            structure_example, indent=0, ensure_ascii=False)
                else:
                    # Fallback for other types
                    base_ex_str = json.dumps(
                        base_ex, indent=0, ensure_ascii=False)

                gemini_prompt = f"""Create {num_questions} {language}-Mongolian translation exercises about "{topic}".

REQUIREMENTS:
1. Match the JSON structure exactly
2. {num_questions} questions in the questions array
3. Mix of {language}→Mongolian and Mongolian→{language} translations
4. Use topic: {topic}
5. Vary question_mode (TRANSLATE, CHOOSE, TYPE)
6. Mongolian text uses "TEXT" or "TEXT_AUDIO" type
7. Valid JSON only, no explanations

STRUCTURE:
{base_ex_str}

OUTPUT: Complete valid JSON object matching this structure."""

                logger.debug(f"Prompt length: {len(gemini_prompt)}")

            except Exception as e:
                logger.error(f"Error creating prompt: {e}")
                return jsonify({"error": f"Failed to create prompt: {str(e)}"}), 500

            # Step 6: Call Gemini API
            logger.debug("Step 6: Calling Gemini API")
            try:
                response = model.generate_content(
                    gemini_prompt,
                    generation_config={
                        'temperature': 0.5,        # Lower temperature for more consistent JSON
                        'max_output_tokens': 8192,  # Even larger for complex exercises
                        'top_p': 0.9,             # Higher top_p for more complete responses
                        'top_k': 20               # Lower top_k for more focused output
                    }
                )

                if not response or not response.text:
                    logger.error("Empty response from Gemini")
                    return jsonify({"error": "Empty response from Gemini API"}), 500

                generated_text = response.text.strip()
                logger.info(
                    f"✅ Gemini API call successful, response length: {len(generated_text)}")
                logger.debug(f"First 100 chars: {generated_text[:100]}")

            except Exception as e:
                logger.error(f"Gemini API call failed: {e}")
                logger.error(f"Error type: {type(e)}")
                return jsonify({
                    "error": f"Gemini API failed: {str(e)}",
                    "error_type": str(type(e))
                }), 500

                # Step 7: Parse JSON response
            logger.debug("Step 7: Parsing JSON response")
            try:
                # Log the full response for debugging
                logger.debug(f"Full response: {generated_text}")

                # Check if response is truncated or incomplete
                if len(generated_text.strip()) < 20:
                    logger.error("Response too short, likely incomplete")
                    return jsonify({"error": "Gemini response was too short/incomplete"}), 500

                # Clean up response text
                clean_text = generated_text.strip()

                # Remove code block markers if present
                if '```json' in clean_text:
                    start = clean_text.find('```json') + 7
                    end = clean_text.find('```', start)
                    if end > start:
                        clean_text = clean_text[start:end].strip()
                        logger.debug("Removed ```json``` markers")
                elif '```' in clean_text:
                    start = clean_text.find('```') + 3
                    end = clean_text.find('```', start)
                    if end > start:
                        clean_text = clean_text[start:end].strip()
                        logger.debug("Removed ``` markers")

                # Find JSON content
                json_start = clean_text.find('{')
                json_end = clean_text.rfind('}') + 1

                if json_start >= 0 and json_end > json_start:
                    clean_text = clean_text[json_start:json_end]
                    logger.debug(f"Extracted JSON length: {len(clean_text)}")
                else:
                    logger.error("Could not find valid JSON boundaries")
                    logger.error(
                        f"json_start: {json_start}, json_end: {json_end}")
                    return jsonify({
                        "error": "Could not extract JSON from response",
                        "raw_response": generated_text[:300]
                    }), 500

                # Validate JSON structure before parsing
                if not clean_text.strip():
                    logger.error("Empty JSON content after extraction")
                    return jsonify({"error": "Empty JSON content"}), 500

                    logger.debug(f"Final JSON to parse: {clean_text[:200]}...")

                # Try to repair common JSON issues before parsing
                def repair_json(text):
                    """Attempt to repair common JSON formatting issues"""
                    # Remove trailing commas
                    import re
                    text = re.sub(r',(\s*[}\]])', r'\1', text)

                    # Ensure proper closing of arrays and objects
                    open_braces = text.count('{')
                    close_braces = text.count('}')
                    open_brackets = text.count('[')
                    close_brackets = text.count(']')

                    # Add missing closing braces/brackets
                    if open_braces > close_braces:
                        text += '}' * (open_braces - close_braces)
                    if open_brackets > close_brackets:
                        text += ']' * (open_brackets - close_brackets)

                    return text

                # Try parsing original first, then repaired version
                try:
                    generated_questions = json.loads(clean_text)
                    logger.debug("JSON parsed successfully on first attempt")
                except json.JSONDecodeError as first_error:
                    logger.warning(f"First JSON parse failed: {first_error}")
                    logger.debug("Attempting to repair JSON...")

                    try:
                        repaired_text = repair_json(clean_text)
                        generated_questions = json.loads(repaired_text)
                        logger.info("JSON parsed successfully after repair")
                    except json.JSONDecodeError as second_error:
                        logger.error(
                            f"JSON repair also failed: {second_error}")
                        # Try to extract just the first complete object
                        try:
                            # Find the first complete JSON object
                            brace_count = 0
                            end_pos = 0
                            for i, char in enumerate(clean_text):
                                if char == '{':
                                    brace_count += 1
                                elif char == '}':
                                    brace_count -= 1
                                    if brace_count == 0:
                                        end_pos = i + 1
                                        break

                            if end_pos > 0:
                                partial_json = clean_text[:end_pos]
                                generated_questions = json.loads(partial_json)
                                logger.info(
                                    "Successfully extracted partial JSON")
                            else:
                                raise json.JSONDecodeError(
                                    "Could not extract valid JSON", clean_text, 0)
                        except:
                            raise second_error
                logger.info("✅ JSON parsing successful")

                return jsonify({
                    "success": True,
                    "generated_questions": generated_questions,
                    "mode": "fast_local"
                })

            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing failed: {e}")
                logger.error(
                    f"Raw response (first 500 chars): {generated_text[:500]}")
                return jsonify({
                    "error": f"Could not parse response as JSON: {str(e)}",
                    "raw_response": generated_text[:200] + "..." if len(generated_text) > 200 else generated_text
                }), 500

        except Exception as e:
            logger.error(f"Unexpected error in generate_fast: {e}")
            logger.exception("Full traceback:")
            return jsonify({
                "error": f"Server error: {str(e)}",
                "error_type": str(type(e))
            }), 500

        finally:
            logger.info("=== FAST GENERATION REQUEST END ===")

    @app.route('/generate', methods=['POST'])
    def generate_normal():
        """Normal generation mode (same as fast but with different config)"""
        logger.info("Normal generation requested - redirecting to fast mode")
        return generate_fast()  # For now, both use same logic

    return app


def main():
    """Main function to run the app locally"""
    print("🚀 AI Question Generator - Local Development Mode")
    print("📋 Make sure to set your GEMINI_API_KEY environment variable")
    print("🌐 The app will be available at: http://localhost:5000")
    print("📝 Logs are saved to app.log")
    print("-" * 60)

    app = create_app()

    try:
        # Run on localhost for local development
        app.run(
            host='127.0.0.1',
            port=5000,
            debug=True,  # Enable debug mode for development
            use_reloader=False  # Prevent double startup
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")


if __name__ == "__main__":
    main()
