#!/usr/bin/env bash
# setup.sh — configure the Logfare route for Radnex.
#
#   ./setup.sh
#
# Finds a Logfare credential (reusing an existing profile or
# $ANTHROPIC_AUTH_TOKEN if present, otherwise prompting for one), writes the
# profile to ~/.radnex/logfare/source with mode 600, installs the LiteLLM
# proxy if it is missing, starts it, and verifies the route end to end.
#
# The venv is the user's own: activate it, `pip install -r requirements.txt`,
# then run this. Idempotent. The key is never echoed back and never leaves this
# machine.

set -euo pipefail

SELF="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
RADNEX_HOME="${RADNEX_HOME:-$HOME/.radnex}"
LOG_DIR="$RADNEX_HOME/logfare"
PROFILE="$LOG_DIR/source"
CONFIG="$LOG_DIR/litellm-config.yaml"
SERVICE="$LOG_DIR/start-litellm.sh"
PORT="${LITELLM_PORT:-4001}"

# The interpreter that carries Radnex's dependencies.
#
# Prefer the checkout's own venv — the one install.sh builds — so `./setup.sh`
# works with no activation after a global install. Then an activated venv
# ($VIRTUAL_ENV), then a python3 on PATH. This script never creates a venv.
_self_dir="$(cd -- "$(dirname -- "$(readlink -f -- "${BASH_SOURCE[0]}")")" && pwd -P)"
_root="${RADNEX_ROOT:-$_self_dir}"
if [[ -x "$_root/.venv/bin/python" ]]; then
  PY="$_root/.venv/bin/python"
elif [[ -n "${VIRTUAL_ENV:-}" && -x "$VIRTUAL_ENV/bin/python" ]]; then
  PY="$VIRTUAL_ENV/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PY="$(command -v python3)"
else
  PY=""
fi

bold() { printf '\033[1m%s\033[0m\n' "$*"; }
step() { printf '\n\033[36m▸\033[0m \033[1m%s\033[0m\n' "$*"; }
ok()   { printf '  \033[32m✔\033[0m %s\n' "$*"; }
warn() { printf '  \033[33m⚠\033[0m %s\n' "$*" >&2; }
die()  { printf '\n\033[31m✖ %s\033[0m\n' "$*" >&2; exit 1; }
# A command the user should run by hand. stderr, like the warnings around it.
note() { printf '      \033[36m%s\033[0m\n' "$*" >&2; }

bold "╭──────────────────────────────────────────────╮"
bold "│  RADNEX · setup                         │"
bold "╰──────────────────────────────────────────────╯"

[[ -n "$PY" ]] || die "no python3 on PATH — create a venv, activate it, then: pip install -r requirements.txt"
command -v curl >/dev/null 2>&1 || die "curl is required."

# The harness must be runnable by this interpreter, or this script would wire
# up a proxy for something that cannot start.
#
# Check the THIRD-PARTY dependencies, not `import radnex`: radnex is
# imported from the checkout itself (see PYTHONPATH below), so `import radnex`
# would succeed from the source tree even in a bare venv with nothing
# installed — passing the check that exists to catch exactly that. The deps are
# what the user's `pip install -r requirements.txt` actually provides.
if ! ( cd / && "$PY" -c 'import anthropic, textual, rich, yaml' ) >/dev/null 2>&1; then
  printf '\n\033[31m✖ Radnex dependencies are not installed for %s\033[0m\n\n' "$PY" >&2
  printf '  Activate your venv and install them, then re-run ./setup.sh:\n\n' >&2
  note "python3 -m venv .venv && source .venv/bin/activate"
  note "pip install -r requirements.txt"
  printf '\n' >&2
  exit 1
fi

# --- 1. select gateway & locate/prompt for credential ------------------------

step "Configuring AI Gateway"

EXISTING_GW=""
for g in apinex radox openrouter unorouter aihubmix tokenharbour logfare; do
  if [[ -f "$RADNEX_HOME/$g/source" ]]; then
    EXISTING_GW="$g"
    break
  fi
done

GW_CHOICE=""
if [[ -n "$EXISTING_GW" ]]; then
  ok "found existing profile for $EXISTING_GW at $RADNEX_HOME/$EXISTING_GW/source"
  printf '  Press Enter to keep current configuration, or type [r] to reconfigure: '
  read -r RECONF || true
  if [[ "$RECONF" != "r" && "$RECONF" != "R" ]]; then
    GW_CHOICE="keep"
  fi
fi

if [[ -z "$GW_CHOICE" ]]; then
  printf '\n  Select an AI Gateway to configure:\n\n'
  printf '  [1] APInex       (https://apinex.bond/  · Free models: DeepSeek-V4.1, Gemini 2.5) [Recommended]\n'
  printf '  [2] Radox AI     (https://radoxai.com/  · Free models: DeepSeek-V3, Gemini 2.0, Claude Haiku)\n'
  printf '  [3] OpenRouter   (https://openrouter.ai/ · Free models: DeepSeek, Llama, Qwen)\n'
  printf '  [4] UnoRouter    (Hosted redundant gateway · Free models)\n'
  printf '  [5] AIHubMix     (Multi-model bridge · Free models)\n'
  printf '  [6] TokenHarbour (High-speed streaming · Free models)\n'
  printf '  [7] Logfare      (Local LiteLLM proxy :4001)\n'
  printf '  [8] AntSeed P2P  (Local buyer on :8377 · No key needed)\n\n'
  printf '  Choice [1-8]: '
  read -r GW_CHOICE || GW_CHOICE="1"
fi

KEY=""
if [[ "$GW_CHOICE" == "1" ]]; then
  printf '\n  Paste your APInex API Key (get one free at https://apinex.bond/):\n  key: '
  read -r KEY || true
  [[ -n "$KEY" ]] || die "no key entered."
  mkdir -p "$RADNEX_HOME/apinex"
  (
    umask 077
    cat > "$RADNEX_HOME/apinex/source" <<EOF
# Radnex — APInex profile
export ANTHROPIC_BASE_URL="https://api.apinex.bond"
export ANTHROPIC_AUTH_TOKEN="$KEY"
export ANTHROPIC_MODEL="deepseek-v4.1-flash"
export ANTHROPIC_API_KEY=""
EOF
  )
  chmod 600 "$RADNEX_HOME/apinex/source"
  printf '%s\n' "apinex" > "$RADNEX_HOME/current-source"
  ok "$RADNEX_HOME/apinex/source (mode 600)"
elif [[ "$GW_CHOICE" == "2" ]]; then
  printf '\n  Paste your Radox AI API Key (get one free at https://radoxai.com/):\n  key: '
  read -r KEY || true
  [[ -n "$KEY" ]] || die "no key entered."
  mkdir -p "$RADNEX_HOME/radox"
  (
    umask 077
    cat > "$RADNEX_HOME/radox/source" <<EOF
# Radnex — Radox AI profile
export ANTHROPIC_BASE_URL="https://api.radoxai.com"
export ANTHROPIC_AUTH_TOKEN="$KEY"
export ANTHROPIC_MODEL="deepseek-v3"
export ANTHROPIC_API_KEY=""
EOF
  )
  chmod 600 "$RADNEX_HOME/radox/source"
  printf '%s\n' "radox" > "$RADNEX_HOME/current-source"
  ok "$RADNEX_HOME/radox/source (mode 600)"
elif [[ "$GW_CHOICE" == "3" ]]; then
  printf '\n  Paste your OpenRouter API Key (https://openrouter.ai/):\n  key: '
  read -r KEY || true
  [[ -n "$KEY" ]] || die "no key entered."
  mkdir -p "$RADNEX_HOME/openrouter"
  (
    umask 077
    cat > "$RADNEX_HOME/openrouter/source" <<EOF
# Radnex — OpenRouter profile
export ANTHROPIC_BASE_URL="https://openrouter.ai/api"
export ANTHROPIC_AUTH_TOKEN="$KEY"
export ANTHROPIC_MODEL="deepseek/deepseek-v4.1:free"
export ANTHROPIC_API_KEY=""
EOF
  )
  chmod 600 "$RADNEX_HOME/openrouter/source"
  printf '%s\n' "openrouter" > "$RADNEX_HOME/current-source"
  ok "$RADNEX_HOME/openrouter/source (mode 600)"
elif [[ "$GW_CHOICE" == "4" ]]; then
  printf '\n  Paste your UnoRouter API Key:\n  key: '
  read -r KEY || true
  [[ -n "$KEY" ]] || die "no key entered."
  mkdir -p "$RADNEX_HOME/unorouter"
  (
    umask 077
    cat > "$RADNEX_HOME/unorouter/source" <<EOF
# Radnex — UnoRouter profile
export ANTHROPIC_BASE_URL="https://api.unorouter.com"
export ANTHROPIC_AUTH_TOKEN="$KEY"
export ANTHROPIC_MODEL="deepseek/deepseek-chat:free"
export ANTHROPIC_API_KEY=""
EOF
  )
  chmod 600 "$RADNEX_HOME/unorouter/source"
  printf '%s\n' "unorouter" > "$RADNEX_HOME/current-source"
  ok "$RADNEX_HOME/unorouter/source (mode 600)"
elif [[ "$GW_CHOICE" == "5" ]]; then
  printf '\n  Paste your AIHubMix API Key:\n  key: '
  read -r KEY || true
  [[ -n "$KEY" ]] || die "no key entered."
  mkdir -p "$RADNEX_HOME/aihubmix"
  (
    umask 077
    cat > "$RADNEX_HOME/aihubmix/source" <<EOF
# Radnex — AIHubMix profile
export ANTHROPIC_BASE_URL="https://aihubmix.com"
export ANTHROPIC_AUTH_TOKEN="$KEY"
export ANTHROPIC_MODEL="coding-glm-5.3-flash-free"
export ANTHROPIC_API_KEY=""
EOF
  )
  chmod 600 "$RADNEX_HOME/aihubmix/source"
  printf '%s\n' "aihubmix" > "$RADNEX_HOME/current-source"
  ok "$RADNEX_HOME/aihubmix/source (mode 600)"
elif [[ "$GW_CHOICE" == "6" ]]; then
  printf '\n  Paste your TokenHarbour API Key:\n  key: '
  read -r KEY || true
  [[ -n "$KEY" ]] || die "no key entered."
  mkdir -p "$RADNEX_HOME/tokenharbour"
  (
    umask 077
    cat > "$RADNEX_HOME/tokenharbour/source" <<EOF
# Radnex — TokenHarbour profile
export ANTHROPIC_BASE_URL="https://api.tokenharbour.net"
export ANTHROPIC_AUTH_TOKEN="$KEY"
export ANTHROPIC_MODEL="deepseek-chat-free"
export ANTHROPIC_API_KEY=""
EOF
  )
  chmod 600 "$RADNEX_HOME/tokenharbour/source"
  printf '%s\n' "tokenharbour" > "$RADNEX_HOME/current-source"
  ok "$RADNEX_HOME/tokenharbour/source (mode 600)"
elif [[ "$GW_CHOICE" == "8" ]]; then
  printf '%s\n' "antseed" > "$RADNEX_HOME/current-source"
  ok "AntSeed P2P selected"
elif [[ "$GW_CHOICE" == "7" ]]; then
  printf '\n  Paste your Logfare API key (starts with lfu_):\n  key: '
  read -rs KEY || true
  printf '\n'
  [[ -n "$KEY" ]] || die "no key entered."
  mkdir -p "$LOG_DIR"
  (
    umask 077
    cat > "$PROFILE" <<EOF
# Radnex — Logfare profile (generated by setup.sh)
export ANTHROPIC_BASE_URL="http://localhost:$PORT"
export ANTHROPIC_AUTH_TOKEN="$KEY"
export ANTHROPIC_MODEL="deepseek-v4.1-flash"
export ANTHROPIC_API_KEY=""
EOF
  )
  chmod 600 "$PROFILE"
  printf '%s\n' "logfare" > "$RADNEX_HOME/current-source"
  ok "$PROFILE (mode 600)"
fi

# --- 3. proxy files ----------------------------------------------------------

step "Checking the proxy files"

# These are shipped artifacts, not user config: the catalog and the manager are
# maintained in packaging/ and an install has to track them. Copying only when
# the file is *missing* left every existing install frozen at whatever it first
# received — so a fix in packaging/ (a required config key, a pidfile guard)
# never reached the copy that actually runs, and the proxy kept failing on a bug
# that was already fixed in the tree. Sync on content instead, but keep a .bak
# of any locally-edited copy rather than silently overwriting someone's work.
sync_shipped() {
  local src="$1" dst="$2" mode="${3:-}"
  if [[ ! -f "$src" ]]; then
    warn "missing from packaging/: $(basename "$src") — leaving $dst alone"
    return 0
  fi
  if [[ ! -f "$dst" ]]; then
    cp -f "$src" "$dst"; [[ -n "$mode" ]] && chmod "$mode" "$dst"
    ok "installed $(basename "$dst")"
  elif cmp -s "$src" "$dst"; then
    [[ -n "$mode" ]] && chmod "$mode" "$dst"
    ok "$(basename "$dst") up to date"
  else
    cp -f "$dst" "$dst.bak"
    cp -f "$src" "$dst"; [[ -n "$mode" ]] && chmod "$mode" "$dst"
    warn "$(basename "$dst") updated — previous copy kept at $dst.bak"
  fi
}

sync_shipped "$SELF/packaging/logfare/litellm-config.yaml" "$CONFIG"
sync_shipped "$SELF/packaging/logfare/start-litellm.sh"     "$SERVICE" 755

# The Token Juice route is a sibling install, not a variant: its own port,
# profile and manager. This step only lays the files down — it does not start
# anything or ask for a credential, because the route ships with a working
# profile and is used on demand via /zim-tokenjuice. Without it a machine that
# ran setup.sh but never laid the route files down would have no Token Juice
# route at all.
TJ_DIR="$RADNEX_HOME/tokenjuice"
if [[ -d "$SELF/packaging/tokenjuice" ]]; then
  mkdir -p "$TJ_DIR"
  sync_shipped "$SELF/packaging/tokenjuice/litellm-config.yaml" "$TJ_DIR/litellm-config.yaml"
  sync_shipped "$SELF/packaging/tokenjuice/start-litellm.sh"    "$TJ_DIR/start-litellm.sh" 755
  sync_shipped "$SELF/packaging/tokenjuice/source.example"      "$TJ_DIR/source.example"
  if [[ ! -f "$TJ_DIR/source" && -f "$SELF/packaging/tokenjuice/source" ]]; then
    ( umask 077; cp -f "$SELF/packaging/tokenjuice/source" "$TJ_DIR/source" )
    chmod 600 "$TJ_DIR/source"
  fi
  ok "installed tokenjuice route (:4000)"
else
  warn "no tokenjuice packaging — /zim-tokenjuice will be unavailable"
fi

# The doctrine file zim mode follows. Installed into RADNEX_HOME so that
# `radnex --mode zim` works from ANY directory: without a copy here, a session
# opened in an unrelated project finds no AGENTS.md and silently falls back to
# the default prompt. A project's own AGENTS.md still wins — the workdir is
# searched first — so this is a fallback, not an override.
#
# Synced on content like the proxy files, but a locally-edited copy is kept as
# .bak rather than overwritten silently: the operator may have tuned their
# doctrine, and that is the one file here that is genuinely theirs.
if [[ -f "$SELF/AGENTS.md" ]]; then
  sync_shipped "$SELF/AGENTS.md" "$RADNEX_HOME/AGENTS.md"
else
  warn "no AGENTS.md in the checkout — zim mode will fall back to the default prompt"
fi

# --- 3b. pagekite (worldwide /phish forwarder) -------------------------------

step "Checking PageKite"
PK_DIR="$RADNEX_HOME/pagekite"
mkdir -p "$PK_DIR"
if [[ -f "$SELF/packaging/pagekite/pagekite.py" ]]; then
  sync_shipped "$SELF/packaging/pagekite/pagekite.py" "$PK_DIR/pagekite.py" 755
else
  printf '  downloading pagekite.py...\n'
  if curl -fsSL -o "$PK_DIR/pagekite.py" https://pagekite.net/pk/pagekite.py; then
    chmod 755 "$PK_DIR/pagekite.py"
    ok "downloaded $PK_DIR/pagekite.py"
  else
    warn "could not download pagekite.py — /phish will fall back to cloudflared/ngrok"
  fi
fi
if [[ ! -f "$RADNEX_HOME/pagekite.name" ]]; then
  warn "no kite name at $RADNEX_HOME/pagekite.name"
  warn "write your kite (e.g. radnex.pagekite.me) there, or export PAGEKITE_NAME."
  warn "first-time signup:  $PK_DIR/pagekite.py --signup"
else
  ok "kite name: $(tr -d '[:space:]' < "$RADNEX_HOME/pagekite.name")"
fi

# Only configure and run LiteLLM if Logfare local proxy was selected
if [[ "$GW_CHOICE" == "7" || ( "$EXISTING_GW" == "logfare" && "$GW_CHOICE" == "keep" ) ]]; then

  # --- 4. litellm --------------------------------------------------------------

  # The proxy gets its OWN venv. It cannot live in the harness's: litellm[proxy]
  # requires rich<14.0 and textual 8.x requires rich>=14.2, so an environment
  # holding both cannot resolve at all. start-litellm.sh already looks in
  # $RADNEX_HOME/venv, so that is where this goes. A litellm that already
  # exists anywhere is reused rather than duplicated.
  PROXY_VENV="$RADNEX_HOME/venv"
  PROXY_PY="$PROXY_VENV/bin/python"

  step "Checking the LiteLLM proxy"
  if command -v litellm >/dev/null 2>&1; then
    ok "litellm on PATH"
  elif [[ -x "$HOME/.local/bin/litellm" ]]; then
    ok "litellm present at ~/.local/bin/litellm"
  elif [[ -x "$PROXY_PY" ]] && "$PROXY_PY" -c 'import litellm' >/dev/null 2>&1; then
    ok "litellm in $PROXY_VENV"
  else
    printf '  building the proxy venv at %s (this can take a minute)...\n' "$PROXY_VENV"
    "$PY" -m venv "$PROXY_VENV" || die "could not create $PROXY_VENV"
    "$PROXY_PY" -m pip install --quiet --disable-pip-version-check --upgrade pip || true
    "$PROXY_PY" -m pip install --quiet --disable-pip-version-check \
      "litellm[proxy]>=1.100.1" "uvloop>=0.22.1" </dev/null \
      || die "could not install litellm[proxy] into $PROXY_VENV"
    ok "litellm installed into $PROXY_VENV"
  fi

  # --- 5. start the proxy ------------------------------------------------------

  step "Starting the proxy on :$PORT"
  if curl -s -o /dev/null -w '%{http_code}' \
       "http://127.0.0.1:$PORT/health/liveliness" --max-time 2 | grep -q 200; then
    ok "a proxy is already serving :$PORT — reusing it"
  elif "$SERVICE" start; then
    ok "proxy healthy on :$PORT"
  else
    warn "proxy did not start — see /tmp/litellm-radnex.log"
    warn "continuing; the launcher will retry on next run."
  fi

  # --- 6. verify the route -----------------------------------------------------

  step "Verifying the route"
  if curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$PORT/health/liveliness" --max-time 3 | grep -q 200; then
    ok "proxy answers on :$PORT"
  else
    warn "proxy not answering yet"
  fi

  BODY='{"model":"deepseek-v4.1-flash","max_tokens":8,"messages":[{"role":"user","content":"say ok"}]}'
  probe() {
    curl -s -o /tmp/radnex-setup-probe.json -w '%{http_code}' \
      -X POST "http://127.0.0.1:$PORT/v1/messages" \
      -H "content-type: application/json" \
      -H "anthropic-version: 2023-06-01" \
      -H "x-api-key: $KEY" \
      --max-time 30 -d "$BODY" || true
  }
  CODE="$(probe)"
  if [[ "$CODE" != "200" ]]; then
    printf '  upstream busy (HTTP %s) — retrying once...\n' "$CODE"
    sleep 3
    CODE="$(probe)"
  fi
  if [[ "$CODE" == "200" ]]; then
    ok "live request through the proxy succeeded"
  else
    warn "live request returned HTTP $CODE"
    head -c 300 /tmp/radnex-setup-probe.json 2>/dev/null; printf '\n'
  fi
  rm -f /tmp/radnex-setup-probe.json
fi

# --- done --------------------------------------------------------------------

printf '\n'
bold "╭──────────────────────────────────────────────╮"
bold "│  setup complete.                             │"
bold "╰──────────────────────────────────────────────╯"
printf '\n'
printf '    \033[36mradnex\033[0m                 # launch\n'
printf '    \033[36mradnex -C ~/proj\033[0m       # run against another directory\n'
printf '    \033[36mradnex --mode cpss\033[0m     # full auto, follows AGENTS.md doctrine\n\n'
