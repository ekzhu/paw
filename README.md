# paw

A terminal chat UI for [QwenPaw](https://github.com/agentscope-ai/QwenPaw).

`paw` is a small, fast [Textual](https://textual.textualize.io/) front-end that
drives a QwenPaw agent over **ACP** (Agent Client Protocol). It streams replies
and thinking, renders tool calls as inline panels, handles permission prompts,
and forwards slash commands (`/model`, `/clear`, `/compact`, …) straight to the
agent.

It deliberately **does not import the QwenPaw backend** — it only speaks ACP — so
it stays light and is released independently of QwenPaw.

```
┌ paw · agent: default · qwen3-max · session a1b2c3 ───────── ⏺ ready ┐
│  you  ▸ summarize today's unread newsletters                        │
│  paw                                                                 │
│  Here's what I found across your 3 sources…                          │
│  ┌ ● 🔧 read_inbox (read)  completed ──────────────────────┐         │
│  │ 12 messages, 3 unread                                    │         │
│  └──────────────────────────────────────────────────────────┘        │
│  ▌ (streaming…)                                                       │
├──────────────────────────────────────────────────────────────────────┤
│ › type a message  (/ commands · ⏎ send · esc interrupt · ⌃c quit)    │
└──────────────────────────────────────────────────────────────────────┘
```

## Install

**Light** — you already have (or will install) QwenPaw:

```bash
pip install qwenpaw-tui   # expects `qwenpaw` on PATH or in the same env
```

**Bundled** — install QwenPaw alongside paw in one go:

```bash
pip install "qwenpaw-tui[bundled]"   # pulls qwenpaw too; works with no separate install
```

Remote-only users (driving a QwenPaw on another machine) need only the light
install.

## Usage

```bash
paw                              # interactive chat with a local/bundled QwenPaw
paw --agent writer               # pick a specific agent
paw -p "what's on my calendar?"  # one-shot: print the answer and exit

paw --remote ssh://me@host       # drive QwenPaw on a remote host over SSH (ACP)
paw --agent-cmd "qwenpaw acp"    # drive an explicit ACP command
```

Inside the chat: `⏎` send, `esc` interrupt the current turn, `ctrl+c` quit.
Slash commands are forwarded to the agent. Type `/` to open a suggestion
dropdown of the agent's commands (the agent advertises them over ACP) — `↑`/`↓`
to pick, `⏎`/`⇥` to insert, `esc` to dismiss; an inline ghost completion of the
top match is also shown (`→` accepts it).

## How it finds QwenPaw

`paw` resolves the agent to drive in this order:

1. `--agent-cmd "<command>"` — used verbatim.
2. `--remote ssh://[user@]host[:port]` — runs `qwenpaw acp` on the remote host
   over SSH (ACP/stdio tunnelled through ssh).
3. **Bundled** — if `qwenpaw` is importable in paw's environment
   (`paw[bundled]`), runs `python -m qwenpaw acp`.
4. **PATH** — runs `qwenpaw acp`.

Or skip ACP entirely and attach to a **networked `qwenpaw app` server** over
HTTP/SSE:

```bash
paw --remote http://host:8088              # or https://
paw --remote https://host --token "$TOK"   # if the server has auth enabled
```

This streams over `POST /api/console/chat`, stops via the stop endpoint, and
polls for tool-approval prompts — no QwenPaw install needed on the paw side.

## How it works

`paw` is an ACP **client**. It spawns the QwenPaw agent as a subprocess (or over
SSH) and exchanges JSON-RPC over stdio. Because QwenPaw already ships a full ACP
agent (`qwenpaw acp`), paw reuses the entire backend — tools, memory, slash
commands, permissions, model switching — without re-implementing any of it.

The agent's stderr is drained to a log file under paw's state dir
(`PAW_STATE_DIR`, or an OS default) so chatty tools (e.g. a headless browser)
can't deadlock the stdio stream.

## Develop

```bash
pip install -e ".[dev]"
pytest            # unit + transport + UI + CLI tests
```

## License

MIT
