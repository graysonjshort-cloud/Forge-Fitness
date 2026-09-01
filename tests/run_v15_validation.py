from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ti=(ROOT/"training_intelligence_v14.py").read_text()
api=(ROOT/"fitness_backend_api_v2_connected.py").read_text()
db=(ROOT/"database.py").read_text()
required=["training_response_engine","muscle_response_model","exercise_effectiveness_engine","adaptive_program_optimizer","program_review","adaptive_training_system"]
for name in required: assert f"def {name}(" in ti, name
routes=["/me/training/response","/me/training/muscle-response","/me/training/exercise-effectiveness","/me/training/program-optimizer","/me/training/program-review","/me/training/adaptive-system"]
for route in routes: assert route in api, route
assert "get_programming_authority" in ti
assert "may_auto_apply" in ti and "auto_apply" in ti
assert "programming_authority" in db
assert '"profile","plan","workout","performance","recovery","response","strategy","next_plan"' in ti
print("v15 closed-loop architecture validation passed")
