# "Ask MindYards" assistant

A small Cloudflare Worker that powers the chat widget on mindyards.in. It answers from
`knowledge.md`, a plain-text digest of the whole site that `build.py` regenerates on every
build, using the Claude API. Nothing about the visitor is stored.

The widget stays hidden until `CONFIG["assistant"]` in `build.py` is set to the worker URL.

## One-time setup (about 15 minutes)

Prerequisites: a free Cloudflare account and an Anthropic API key from https://platform.claude.com.

```bash
cd worker
npm install @anthropic-ai/sdk
npm install --save-dev wrangler
npx wrangler login
npx wrangler secret put ANTHROPIC_API_KEY      # paste the key when prompted
npx wrangler deploy
```

The deploy prints a URL such as `https://mindyards-assistant.<account>.workers.dev`.
Put that URL in `build.py`:

```python
CONFIG = {
    ...
    "assistant": "https://mindyards-assistant.<account>.workers.dev",
}
```

then rebuild and push:

```bash
python build.py
git add -A && git commit -m "Switch on the site assistant" && git push
```

## Updating the knowledge

Every `python build.py` rewrites `worker/knowledge.md` from the site content. After a content
change, run `npx wrangler deploy` again from this folder so the assistant knows about it.

## Cost and limits

- Model: `claude-opus-5-5` by default (`MODEL` in `wrangler.toml`). `claude-haiku-5-5` is about
  40 times cheaper and fine for this use; change the variable and redeploy.
- The site digest is sent with prompt caching, so repeat questions within a few minutes cost a
  fraction of the first one.
- `fallbacks: "default"` is enabled: if the model's safety classifier declines a question, the
  API retries on a fallback model inside the same call. Remove the `betas` and `fallbacks` lines
  in `assistant.js` if you would rather it simply refuse.
- Rate limit: 20 questions per minute per visitor IP (`[[ratelimits]]` in `wrangler.toml`).
- Only requests from mindyards.in (and the local preview) are accepted (`ALLOWED_ORIGINS`).

## Local test

```bash
npx wrangler dev          # serves on http://localhost:8787
curl -X POST http://localhost:8787 -H "Origin: http://127.0.0.1:8765" -H "Content-Type: application/json" \
  -d "{\"messages\":[{\"role\":\"user\",\"content\":\"What do you do?\"}],\"page\":\"/\"}"
```
