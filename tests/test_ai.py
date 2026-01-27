import os
from scheduler.ai import parse_user_input

def test_ai_parsing():
    print("Testing Gemini Intake...")
    
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY not found. Please export it in your terminal.")
        return

    # User input scenario
    raw_text = "I need to debug the login issue (urgent!) and also read that research paper on Transformers for about 2 hours."
    
    print(f"Input: '{raw_text}'")
    
    tasks = parse_user_input(raw_text)
    
    if tasks:
        print(f"✅ Successfully parsed {len(tasks)} tasks:")
        for t in tasks:
            print(f"  - [{t.priority.name}] {t.title} ({t.duration_minutes}m) [{t.category.value}]")
    else:
        print("❌ Failed to parse tasks.")

if __name__ == "__main__":
    test_ai_parsing()
