# Repair v4

Fixed the blank/non-opening app problem.

Cause:
The app called the API before the first render. If the API was unavailable, the startup promise rejected and the UI never rendered, making the page look broken/blank.

Fix:
- Startup is now wrapped in error handling.
- The UI ALWAYS renders even if the API is offline.
- An on-screen connection error shows the exact API address.
- Added a Retry Connection button.
- The rest of v2/v3 repairs are preserved.

Start API first:
py -m uvicorn fitness_backend_api_v2_connected:app --host 0.0.0.0 --port 8000

Then UI:
py -m http.server 5500 --bind 0.0.0.0
