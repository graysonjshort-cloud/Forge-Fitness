from pathlib import Path
r=Path(__file__).resolve().parents[1]
ti=(r/"training_intelligence_v14.py").read_text(); api=(r/"fitness_backend_api_v2_connected.py").read_text()
idx=(r/"index.html").read_text(); sw=(r/"sw.js").read_text(); js=(r/"js/forge_adaptive_v16.js").read_text(); prog=(r/"js/forge_progress_runtime.js").read_text(); app=(r/"app.js").read_text()
for token in ["def adaptive_directives_v5","recovery outranks progression","prefer the smallest effective change","never exceed the user's programming authority"]:
    assert token in ti,token
assert '@app.get("/me/training/adaptive-directives")' in api
assert "/js/forge_adaptive_v16.js?v=16.0.0" in idx
assert "/js/forge_adaptive_v16.js?v=16.0.0" in sw
assert "adaptiveDirectivesCard()" in prog
assert "loadAdaptiveDirectives()" in app
assert (r/"app.js").stat().st_size<100000
print("v16.0 adaptive programming validation passed")
