from app.main import update_summary, construct_prompt

def test_update_summary():
    session = {"summary": "Step 1 done."}
    new_update = "Step 2 ongoing."
    update_summary(session, new_update)
    assert session["summary"] == "Step 1 done. Step 2 ongoing."

def test_construct_prompt():
    session = {"summary": "Step 1 done."}
    latest_update = "Step 2 ongoing."
    prompt = construct_prompt(session, latest_update)
    
    assert "Step 1 done." in prompt["user_prompt"]
    assert "Step 2 ongoing." in prompt["user_prompt"]
    assert "You are a Technical Interviewer" in prompt["system_message"]
