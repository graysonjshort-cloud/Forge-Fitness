# Forge Fitness Connected

This UI is wired to `fitness_backend_api_v2_connected.py`.

## Install dependencies

```cmd
py -m pip install fastapi uvicorn pydantic
```

## Start API (terminal 1)

```cmd
py -m uvicorn fitness_backend_api_v2_connected:app --host 0.0.0.0 --port 8000
```

## Start UI (terminal 2)

```cmd
py -m http.server 5500 --bind 0.0.0.0
```

PC: http://127.0.0.1:5500

Phone on same Wi-Fi: `http://YOUR-PC-IP:5500`

The UI automatically calls `http://YOUR-PC-IP:8000`. Keep both terminal windows open.
