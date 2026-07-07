# Setup

The `scripts/synth_survey.py` and `scripts/synth_usability.py` tools need one
thing: an Ollama-compatible chat endpoint. No API keys, no pip installs — just
Python 3 (stdlib only) and `curl`, both already on macOS/Linux, and available
on Windows via WSL or a native Ollama install.

## 1. Install Ollama

**macOS:**
```bash
brew install ollama
# or download the app: https://ollama.com/download/mac
```

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:**
Download the installer from https://ollama.com/download/windows, or use WSL2
and follow the Linux instructions above.

Start the Ollama server if it isn't already running as a background service:
```bash
ollama serve
```
(On macOS with the Ollama.app installed, this runs automatically in the
background — you generally don't need to run it manually.)

## 2. Pull the model

The scripts default to `gemma4:12b` — a good balance of quality and RAM
footprint (~7.6GB) for running hundreds of simulated respondents locally and
free.

```bash
ollama pull gemma4:12b
```

Any Ollama-compatible model works — pass `--model <tag>` to either script.
Lighter machines can try a smaller model (e.g. `gemma3:4b`, `llama3.2:3b`);
heavier machines with more RAM can go bigger for better-quality personas
(e.g. `gemma4:26b`, `qwen3:14b`). Bigger models produce more coherent,
better-differentiated segment voices, but take longer per call.

## 3. Verify

```bash
curl localhost:11434/api/tags
```

You should get back a JSON list of installed models, including the one you
just pulled. If this fails:
- Confirm Ollama is running: `ollama serve` (or check the menu-bar app on macOS).
- Confirm the port: Ollama defaults to `11434`. If you changed it, pass
  `--endpoint http://localhost:<port>` to the scripts.

Then do a quick end-to-end check:
```bash
curl localhost:11434/api/chat -d '{
  "model": "gemma4:12b",
  "messages": [{"role": "user", "content": "reply with the word OK"}],
  "stream": false
}'
```
You should get a JSON response with `"message":{"content":"OK"...}` (or close
to it — small models sometimes add a word or two).

## No local GPU / low-RAM machine? Use a hosted model instead

Both scripts only need an endpoint that speaks Ollama's `/api/chat` format
(`{model, messages, stream, options}` in → `{message: {content}}` out). If
your machine can't comfortably run a 7-12GB model:

- **Ollama Cloud** — `ollama` itself can proxy to hosted models (e.g.
  `glm-5.2:cloud`, `kimi-k2.5:cloud`) once you're signed in
  (`ollama signin`) — same local endpoint, same `/api/chat` shape, no code
  changes needed. Just pass `--model glm-5.2:cloud` (or whichever cloud tag
  you have access to).
- **A remote Ollama instance** — run Ollama on a bigger machine (a VPS, a
  spare desktop) and point `--endpoint http://<that-host>:11434` at it.
- **Any other Ollama-API-compatible server** — several inference servers
  (e.g. LM Studio in "Ollama compatibility" mode) expose the same
  `/api/chat` shape. If yours does, just point `--endpoint` at it.

The scripts don't hit OpenAI's API shape directly, but anything that mirrors
Ollama's `/api/chat` request/response contract will work as a drop-in swap
via `--endpoint`.

### No local LLM at all? Fall back to hosted Claude

If you can't run a local model and don't have an Ollama-compatible endpoint,
both scripts can call a hosted **Claude** model directly (still stdlib only —
raw HTTPS, no SDK or pip install). Set an API key and they'll use it
automatically when Ollama isn't reachable:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python3 synth_survey.py --personas personas.example.md --concept "..."
# → "Ollama not reachable — falling back to hosted Claude."
```

- Default model is **`claude-sonnet-5`** (best persona quality; a survey is only
  a handful of calls, so cost is negligible). For the cheaper option pass
  `--model claude-haiku-4-5`.
- Force it either way with `--provider anthropic` (or `--provider ollama` to
  require local). Default is `--provider auto` (local first, Claude fallback).
- Get a key at https://console.anthropic.com. Unlike the local path, this sends
  your concept/persona text to Anthropic's API.

## Memory note

Both scripts call Ollama **sequentially** (one segment/persona-task at a
time), not in parallel — this is deliberate so you don't blow past your
machine's RAM running multiple large-model instances at once. A full survey
across 3 segments, or a usability run across 3 personas x 4 tasks, takes a
few minutes on a machine like an M-series Mac with `gemma4:12b`.

## Build engine (highly recommended): GSD

The synthetic-audience tools above are all Forge needs for the **validation**
and **usability** stages, and they work standalone. Forge's **build** stage
(Stage 2) is a different matter: it's designed to run on **GSD**
([`@opengsd/get-shit-done-redux`](https://github.com/open-gsd/gsd-core)),
a public npm package that gives a build durable `.planning/` state, atomic
commits, and verification gates so any session can resume it cold.

GSD is **highly recommended but optional** — Forge falls back to a direct
Claude Code build if it's absent, just with less durable state. `install.sh`
**detects and offers** to install it; you can also add it anytime:

```bash
npx -y @opengsd/get-shit-done-redux@latest --global
```

This needs Node/npm (https://nodejs.org). To confirm it's installed, look for
`gsd-*` skills in `~/.claude/skills/` or the `~/.claude/get-shit-done/` folder.
