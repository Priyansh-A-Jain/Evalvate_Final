import os
import json
import glob
import time
import sys
import google.generativeai as genai

def setup_gemini():
    # Attempt to load from env first
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY environment variable not found.")
        api_key = input("Please enter your Gemini API Key: ").strip()
        if not api_key:
            print("API Key is required to run the conversion script.")
            sys.exit(1)
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.5-flash")

def convert_batch(model, subject, batch_data):
    prompt = f"""
You are a subject matter expert task with rewriting/enriching a question bank JSON dataset for interview pacing and evaluation.
Below is a batch of questions for the subject: "{subject}".
You need to convert each object in the array to the new schema format.

Rules:
1. Retain the "id", "subject", and "difficulty" fields exactly as they are.
2. Rename the "Questions" field to "question".
3. Add a "follow_ups" field which is a list of exactly 3 relevant follow-up questions that an interviewer could ask next.
4. Add an "evaluation_criteria" field which is a list of exactly 3 criteria for evaluating the candidate's response (e.g., ["conceptual_clarity", "technical_depth", "use_of_examples"]).
5. Add an "expected_keywords" field which is a list of 4-6 essential technical keywords, phrases, or concepts that should be present in a good answer.
6. Add a "type" field which represents the question type (choose from: "conceptual", "technical", "scenario", or "practical").

Example Output Format:
{{
  "id": "Q1",
  "subject": "Artificial Intelligence",
  "difficulty": "Easy",
  "question": "What is the relationship between Artificial Intelligence, Machine Learning, and Deep Learning?",
  "follow_ups": [
    "Can you give a real-world example of each?",
    "Where does generative AI fit in this hierarchy?",
    "What's the boundary between ML and Deep Learning in practice?"
  ],
  "evaluation_criteria": ["conceptual_clarity", "use_of_examples", "depth"],
  "expected_keywords": ["neural networks", "subset", "training data", "representation"],
  "type": "conceptual"
}}

Input JSON array to convert:
{json.dumps(batch_data, indent=2)}

Respond with only a valid JSON array of the converted objects. Do not include markdown code block syntax.
"""
    for attempt in range(3):
        try:
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            result = json.loads(response.text.strip())
            if isinstance(result, list):
                return result
            else:
                print(f"Warning: Response was not a list, retrying... (Attempt {attempt+1}/3)")
        except Exception as e:
            wait_time = 65 if "429" in str(e) or "quota" in str(e).lower() else 5
            print(f"Error calling Gemini API: {e}. Retrying in {wait_time} seconds... (Attempt {attempt+1}/3)")
            time.sleep(wait_time)
    
    print("Failed to convert batch after 3 attempts.")
    return None

def process_file(model, file_path):
    print(f"\nProcessing {os.path.basename(file_path)}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Skipping {file_path} because of JSON decode error: {e}")
            return False

    if not isinstance(data, list):
        print(f"Skipping {file_path} because the top-level structure is not a JSON list.")
        return False

    # Check if already processed (heuristic: if 'follow_ups' exists in the first question)
    if len(data) > 0 and 'follow_ups' in data[0]:
        print(f"{os.path.basename(file_path)} is already in the new format. Skipping.")
        return True

    subject = data[0].get("subject", os.path.splitext(os.path.basename(file_path))[0])
    
    # Process in batches of 10 to avoid token limits and stay robust
    batch_size = 10
    converted_data = []
    
    for i in range(0, len(data), batch_size):
        batch = data[i:i+batch_size]
        print(f"  Converting questions {i+1} to {min(i+batch_size, len(data))} of {len(data)}...")
        converted_batch_data = convert_batch(model, subject, batch)
        if converted_batch_data is None:
            print(f"Aborting process for {file_path} due to API issues.")
            return False
        converted_data.extend(converted_batch_data)
        time.sleep(13.0) # Sleep 13s to stay under Gemini free-tier 5 RPM limit

    # Save output back to original file
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(converted_data, f, indent=2)
    print(f"Successfully converted and saved {os.path.basename(file_path)}!")
    return True

def main():
    model = setup_gemini()
    
    # Search for all json files in current directory
    json_files = glob.glob("*.json")
    # Remove AI.json as it's already manually completed
    json_files = [f for f in json_files if os.path.basename(f) != "AI.json"]
    
    print(f"Found {len(json_files)} JSON files to process: {json_files}")
    
    success_count = 0
    for file_path in json_files:
        if process_file(model, file_path):
            success_count += 1
            
    print(f"\nDone! Successfully converted {success_count} / {len(json_files)} files.")

if __name__ == "__main__":
    main()
