# 🌤️ Weather Chatbot (LangGraph + Ollama + Streamlit)

A focused weather assistant that only answers weather-related questions. It uses **LangGraph** for tool routing, **Ollama** for a local LLM, and **WeatherAPI** for live current conditions and forecasts.

## ✨ Features
- ✅ Weather-only responses with a strict system prompt
- 🧰 Two tools: **current weather** and **forecast (N days)**
- 🌡️ Returns temperature (°C), humidity (%), wind (kph), and air quality metrics
- 🧪 Air quality always enabled (`aqi=yes`)
- ⚡ Streamlit chat UI with tool-call details

## 🧱 Project Structure
```
weather-chatbot/
├── README.md
├── pyproject.toml
├── poetry.lock
└── weather-chatbot/
    ├── .env
    ├── app_streamlit.py
    └── core/
        ├── agent/
        │   ├── __init__.py
        │   ├── agent.py
        │   └── tools.py
        ├── config.py
        └── models.py
```

## 🧰 Tools (WeatherAPI)
### 1) Current Weather Tool
- **Endpoint:** `http://api.weatherapi.com/v1/current.json`
- **Inputs:** `city`
- **Returns:** temperature (°C), humidity, wind (kph), air quality

### 2) Forecast Weather Tool
- **Endpoint:** `http://api.weatherapi.com/v1/forecast.json`
- **Inputs:** `city`, `days` (default 3, max 10)
- **Returns:** daily temperature (°C), humidity, wind (kph), air quality

Both tools always send `aqi=yes` and include the API key.

## 🧠 How the Agent Works
- The assistant starts with a **system prompt** that enforces weather-only answers.
- Requests are routed via **LangGraph**:
  - `assistant → tools → assistant`
- The tools call WeatherAPI, normalize the response, and return only the needed fields.

## 🔧 Setup
### 1) Install Dependencies
From the repo root:
```bash
poetry install
```

### 2) Configure Environment Variables
The `.env` lives in `weather-chatbot/.env` (inside the inner folder).

Example:
```env
OLLAMA_BASE_URL=http://localhost:11434/v1
LLM_MODEL=qwen3
LLM_TEMPERATURE=0
LLM_API_KEY=ollama
WEATHER_API_KEY=YOUR_WEATHERAPI_KEY
```

### 3) Start Ollama
Make sure Ollama is running and the model is pulled:
```bash
ollama pull qwen3
ollama serve
```

### 4) Run the App
Run Streamlit from the inner folder so `.env` is picked up:
```bash
cd weather-chatbot
poetry run streamlit run app_streamlit.py
```

## 💬 Example Prompts
- “What is the current weather in Madrid?”
- “Give me the 5-day forecast for Barcelona.”
- “How’s the air quality in Valencia right now?”

If asked something unrelated to weather, it will reply:
> “I can only answer weather related matters.”

## ⚙️ Configuration
All settings are loaded via **python-decouple** from `.env`.

| Variable | Description | Example |
|---|---|---|
| `OLLAMA_BASE_URL` | Ollama OpenAI-compatible base URL | `http://localhost:11434/v1` |
| `LLM_MODEL` | Ollama model name | `qwen3` |
| `LLM_TEMPERATURE` | Sampling temperature | `0` |
| `LLM_API_KEY` | Dummy key for Ollama | `ollama` |
| `WEATHER_API_KEY` | WeatherAPI key | `your_key_here` |

## 🩺 Troubleshooting
- ❌ **Weather API error**: Check `WEATHER_API_KEY` in `.env`.
- ❌ **Connection refused**: Ensure `ollama serve` is running.
- ❌ **Model not found**: Run `ollama pull qwen3` (or your chosen model).
- ❌ **No .env loaded**: Run Streamlit from `weather-chatbot/`.

## 📝 Notes
- The UI streams the assistant response in chunks for a smoother chat experience.
- Forecast days are clamped to **1–10** by the tool.

## 📦 Tech Stack
- 🧠 LangGraph
- 🦙 Ollama (OpenAI-compatible API)
- 🌦️ WeatherAPI
- 🧩 LangChain tools
- 🎨 Streamlit
