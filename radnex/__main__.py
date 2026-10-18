"""Command-line entrypoint: ``python -m radnex`` / ``radnex``."""

from __future__ import annotations

import argparse
import os
import shlex
import sys
from pathlib import Path

from . import __version__
from . import aihubmix as ah_mod
from . import antseed as as_mod
from . import apinex as api_mod
from . import logfare as lf_mod
from . import openrouter as or_mod
from . import radox as rx_mod
from . import sources as sources_mod
from . import session as session_mod
from . import tokenharbour as th_mod
from . import unorouter as uno_mod
from . import update as update_mod
from .config import KNOWN_MODELS, Config, DEFAULT_MODEL, find_agents_file
from .scope import find_legacy_scope
from .theme import THEME_NAMES, current_theme


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="radnex",
        description="Radnex — autonomous security assessment and coding agent with a high-performance terminal UI.",
    )
    parser.add_argument("--model", "-m", default=None, help=f"model name (default: {DEFAULT_MODEL})")
    parser.add_argument("--workdir", "-C", default=None, help="working directory (default: cwd)")
    parser.add_argument("--allow", default=None,
                        help="path to allow.yaml — declared targets; its presence runs tools unattended")
    parser.add_argument("--deny", default=None,
                        help="path to out-of-scope.yaml — hosts that are never touched")
    parser.add_argument("--scope", default=None,
                        help="DEPRECATED — replaced by --allow / --deny; ignored with a warning")
    parser.add_argument("--unsafe", action="store_true",
                        help="disable the filesystem sandbox (paths may escape the workdir)")
    parser.add_argument("--theme", default=None, choices=THEME_NAMES,
                        help="colour theme (system = match the terminal's own colours)")
    parser.add_argument("--rain", action="store_true",
                        help="start with matrix rain on in the shell (off by default for readability)")
    parser.add_argument("--no-rain", action="store_true",
                        help="disable matrix rain entirely, including the boot screen")
    parser.add_argument("--no-think", action="store_true",
                        help="do not show the model's own reasoning when the "
                             "endpoint forwards it (on by default; /think toggles)")
    parser.add_argument("--mode", default=None,
                        choices=["auto", "edits", "plan", "cpss", "zim", "danger", "uncensored"],
                        help="agent mode: auto | edits | plan | cpss | danger | uncensored (default: auto)")
    parser.add_argument("--agents", default=None,
                        help="path to AGENTS.md used by cpss mode (default: workdir, "
                             "its parent, ~/.radnex, then ~)")
    parser.add_argument("--max-tokens", type=int, default=None, help="max output tokens per reply")
    parser.add_argument("--no-auto-compact", action="store_true",
                        help="never compact history automatically; /compact still works")
    parser.add_argument("--no-update", action="store_true",
                        help="skip the launch-time check for new commits on the upstream")
    parser.add_argument("--list-models", action="store_true", help="list known models and exit")
    parser.add_argument("--panes", action="store_true",
                        help="start in a tmux session where ctrl+b h / ctrl+b v open "
                             "another Radnex pane, and the panes' agents can message each other")
    parser.add_argument("--resume", default=None, metavar="SESSION",
                        help="restore a saved session at launch (used by /panes)")
    parser.add_argument("--version", action="version", version=f"radnex {__version__}")
    return parser


def _launcher_path() -> str | None:
    """The launcher script this run came through, if there is one.

    ``packaging/radnex`` exports ``RADNEX_ROOT`` before it execs the
    interpreter, so the script is discoverable from there. A bare
    ``python -m radnex`` — no launcher — leaves the variable unset and gets
    ``None``.
    """
    root = os.environ.get("RADNEX_ROOT")
    if not root:
        return None
    launcher = Path(root) / "packaging" / "radnex"
    if launcher.is_file() and os.access(launcher, os.X_OK):
        return str(launcher)
    return None


#: Flags the tmux *pane* command must not carry. `--panes` would recurse, and
#: `--resume` belongs to the first pane alone — panes opened later are new
#: agents, and giving each of them the same history would defeat the point of
#: them being separate agents that message each other.
_PANE_STRIP_FLAGS = ("--panes",)
_PANE_STRIP_WITH_VALUE = ("--resume",)


def _pane_inner_argv(argv: list[str]) -> list[str]:
    """``argv`` minus the flags that belong to the launcher, not to a pane.

    Handles both ``--resume X`` and ``--resume=X``; anything unrecognised is
    passed through untouched, so an unrelated flag is never eaten.
    """
    out: list[str] = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in _PANE_STRIP_FLAGS:
            i += 1
            continue
        if a in _PANE_STRIP_WITH_VALUE:
            i += 2
            continue
        if any(a.startswith(f + "=") for f in _PANE_STRIP_WITH_VALUE):
            i += 1
            continue
        out.append(a)
        i += 1
    return out


def _interactive_setup(cfg: Config) -> bool:
    """Prompt the operator to select and configure an AI gateway when no keys are found."""
    try:
        print("\n\033[1;36m╭──────────────────────────────────────────────────────────────╮\033[0m")
        print("\033[1;36m│\033[0m  \033[1mRADNEX · AI Gateway & API Key Configuration Wizard\033[0m          \033[1;36m│\033[0m")
        print("\033[1;36m╰──────────────────────────────────────────────────────────────╯\033[0m")
        print("  No AI credentials detected. Select an AI Provider to configure:\n")
        print("  \033[1;32m[1]\033[0m \033[1mAPInex\033[0m       (https://apinex.bond/  · Free models: DeepSeek-V4.1, Gemini 2.5)")
        print("  \033[1;32m[2]\033[0m \033[1mRadox AI\033[0m     (https://radoxai.com/  · Free models: DeepSeek-V3, Gemini 2.0, Claude Haiku)")
        print("  \033[1;32m[3]\033[0m \033[1mOpenRouter\033[0m   (https://openrouter.ai/ · Free models: DeepSeek, Llama, Qwen)")
        print("  \033[1;32m[4]\033[0m \033[1mUnoRouter\033[0m    (Hosted redundant gateway · Free models)")
        print("  \033[1;32m[5]\033[0m \033[1mAIHubMix\033[0m     (Multi-model bridge · Free GLM-5.3, Qwen-3.8)")
        print("  \033[1;32m[6]\033[0m \033[1mTokenHarbour\033[0m (High-capacity stream · Free DeepSeek, Qwen)")
        print("  \033[1;32m[7]\033[0m \033[1mCustom/Anthropic\033[0m (Direct ANTHROPIC_API_KEY / ANTHROPIC_AUTH_TOKEN)")
        print("  \033[1;32m[8]\033[0m \033[1mAntSeed P2P\033[0m  (Local P2P Buyer on :8377 · No key needed)")
        print("  \033[1;31m[0]\033[0m \033[2mExit\033[0m\n")

        choice = input("\033[1mSelect an option [1-8, or 0 to exit]: \033[0m").strip()
        if not choice or choice in ("0", "q", "quit", "exit"):
            return False

        if choice == "1":
            key = input("\n\033[1mPaste your APInex API Key (https://apinex.bond/): \033[0m").strip()
            if not key:
                print("  \033[33m⚠ No key entered. Aborted.\033[0m")
                return False
            path = api_mod.save_key(key)
            api_mod.apply_to(cfg)
            sources_mod.set_current("apinex")
            print(f"  \033[32m✔ APInex configured!\033[0m Key saved to {path}. Active model: {cfg.model}\n")
            return True

        elif choice == "2":
            key = input("\n\033[1mPaste your Radox AI API Key (https://radoxai.com/): \033[0m").strip()
            if not key:
                print("  \033[33m⚠ No key entered. Aborted.\033[0m")
                return False
            path = rx_mod.save_key(key)
            rx_mod.apply_to(cfg)
            sources_mod.set_current("radox")
            print(f"  \033[32m✔ Radox AI configured!\033[0m Key saved to {path}. Active model: {cfg.model}\n")
            return True

        elif choice == "3":
            key = input("\n\033[1mPaste your OpenRouter API Key (https://openrouter.ai/): \033[0m").strip()
            if not key:
                print("  \033[33m⚠ No key entered. Aborted.\033[0m")
                return False
            path = or_mod.save_key(key)
            or_mod.apply_to(cfg)
            sources_mod.set_current("openrouter")
            print(f"  \033[32m✔ OpenRouter configured!\033[0m Key saved to {path}. Active model: {cfg.model}\n")
            return True

        elif choice == "4":
            key = input("\n\033[1mPaste your UnoRouter API Key: \033[0m").strip()
            if not key:
                print("  \033[33m⚠ No key entered. Aborted.\033[0m")
                return False
            path = uno_mod.save_key(key)
            uno_mod.apply_to(cfg)
            sources_mod.set_current("unorouter")
            print(f"  \033[32m✔ UnoRouter configured!\033[0m Key saved to {path}. Active model: {cfg.model}\n")
            return True

        elif choice == "5":
            key = input("\n\033[1mPaste your AIHubMix API Key: \033[0m").strip()
            if not key:
                print("  \033[33m⚠ No key entered. Aborted.\033[0m")
                return False
            path = ah_mod.save_key(key)
            ah_mod.apply_to(cfg)
            sources_mod.set_current("aihubmix")
            print(f"  \033[32m✔ AIHubMix configured!\033[0m Key saved to {path}. Active model: {cfg.model}\n")
            return True

        elif choice == "6":
            key = input("\n\033[1mPaste your TokenHarbour API Key: \033[0m").strip()
            if not key:
                print("  \033[33m⚠ No key entered. Aborted.\033[0m")
                return False
            path = th_mod.save_key(key)
            th_mod.apply_to(cfg)
            sources_mod.set_current("tokenharbour")
            print(f"  \033[32m✔ TokenHarbour configured!\033[0m Key saved to {path}. Active model: {cfg.model}\n")
            return True

        elif choice == "7":
            key = input("\n\033[1mPaste your Custom/Anthropic API Key or Auth Token: \033[0m").strip()
            if not key:
                print("  \033[33m⚠ No key entered. Aborted.\033[0m")
                return False
            cfg.auth_token = key
            cfg.api_key = key
            print("  \033[32m✔ Custom credentials set!\033[0m\n")
            return True

        elif choice == "8":
            as_mod.apply_to(cfg)
            sources_mod.set_current("antseed")
            print("  \033[32m✔ AntSeed P2P selected!\033[0m\n")
            return True

        else:
            print("  \033[33m⚠ Invalid choice.\033[0m")
            return False
    except (KeyboardInterrupt, EOFError):
        print("\n  \033[33mSetup cancelled.\033[0m")
        return False


def main(argv: list[str] | None = None) -> int:
    # Captured before parsing so the re-exec below can reproduce the original
    # invocation exactly, whatever it was.
    raw_argv = list(argv) if argv is not None else sys.argv[1:]

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_models:
        # The live catalog when it can be reached, the declared snapshot when it
        # cannot. This is a one-shot that exits, so one blocking fetch is the
        # right price for a list that is not a month out of date — and a failure
        # is reported on stderr rather than silently printing a stale list as
        # though it were current.
        models, err = lf_mod.model_ids()
        if models is None:
            print(f"radnex: {err} — showing the declared list", file=sys.stderr)
            models = list(KNOWN_MODELS)
        for m in models:
            print(m)
        return 0

    workdir = Path(args.workdir).expanduser() if args.workdir else Path.cwd()

    # --panes: hand the whole session to tmux. tmux owns ctrl+b and the splits;
    # every pane re-runs this same command without --panes, so each one is an
    # ordinary Radnex that happens to share a mailbox with its peers.
    if args.panes and not os.environ.get("RADNEX_PANE_SESSION"):
        from . import panes as panes_mod

        if not panes_mod.tmux_available():
            print("radnex: --panes needs tmux — install it (e.g. `sudo apt install tmux`)",
                  file=sys.stderr)
            return 2
        launcher = _launcher_path()
        base = [launcher] if launcher else [sys.executable, "-m", "radnex"]
        # The pane command keeps everything the operator typed, minus the
        # launcher's own flags — so `radnex --panes --theme amber` opens
        # amber panes. The first pane additionally resumes, when asked.
        zim_cmd = " ".join(shlex.quote(p) for p in [*base, *_pane_inner_argv(raw_argv)])
        first_cmd = zim_cmd
        if args.resume:
            first_cmd = " ".join(shlex.quote(p) for p in [
                *base, "--resume", args.resume, *_pane_inner_argv(raw_argv)])
        state = Path(os.environ.get("RADNEX_HOME") or (Path.home() / ".radnex"))
        conf = panes_mod.write_tmux_conf(state, zim_cmd)
        return panes_mod.launch(conf, zim_cmd, workdir, first_cmd=first_cmd)

    # Target scope: two files with one job each. allow.yaml arms the session
    # (its presence means the operator has declared their targets, so tools run
    # unattended); out-of-scope.yaml is the never-touch list. Each is looked for
    # in the working directory first, then in ~/.radnex.
    def _find(explicit: str | None, names: tuple[str, ...]) -> Path | None:
        if explicit:
            return Path(explicit).expanduser()
        for base in (workdir, Path.home() / ".radnex"):
            for name in names:
                candidate = Path(base) / name
                if candidate.exists():
                    return candidate
        return None

    allow_path = _find(args.allow, ("allow.yaml", "allow.yml"))
    deny_path = _find(args.deny, ("out-of-scope.yaml", "out-of-scope.yml"))

    # A leftover scope.yaml is never read: the old file was an allow-list that
    # also blocked, so reinterpreting it as a deny-list would block the very
    # hosts the operator had declared. Report it instead of acting on it.
    legacy_scope = None
    if args.scope:
        legacy_scope = Path(args.scope).expanduser()
    else:
        legacy_scope = find_legacy_scope(workdir, Path.home())

    # Zim mode follows the operator's AGENTS.md. The search order lives in
    # config.find_agents_file so the CLI and the runtime /mode zim path cannot
    # drift apart: workdir, its parent, the installed doctrine in ~/.radnex,
    # then ~. The installed copy is what makes zim mode work from any directory.
    agents_path = None
    if args.agents:
        agents_path = Path(args.agents).expanduser()
    else:
        agents_path = find_agents_file(workdir)

    # Which theme to open with. An explicit --theme wins; failing that, whatever
    # was last chosen with /theme, so a restart lands back on it; failing both,
    # the config default (green). ``from_env`` ignores None overrides, so
    # resolving the precedence into one value here is what makes the remembered
    # choice take effect — and what keeps ``--theme`` authoritative over it.
    theme = args.theme or current_theme()

    # Shell rain is off unless requested. --no-rain kills rain everywhere,
    # including the boot screen.
    cfg = Config.from_env(
        model=args.model,
        workdir=workdir,
        allow_path=allow_path,
        deny_path=deny_path,
        legacy_scope_path=legacy_scope,
        unsafe=args.unsafe or None,
        theme=theme,
        max_tokens=args.max_tokens,
        # `from_env` applies only non-None overrides, so False is passed
        # explicitly rather than `or None` — otherwise the flag could never turn
        # the feature off, which is its entire job.
        auto_compact=False if args.no_auto_compact else None,
        mode=args.mode,
        agents_path=agents_path,
        rain=True if args.rain else None,
        boot_rain=False if args.no_rain else None,
        show_thinking=False if args.no_think else None,
    )

    # A remembered hosted-gateway choice has to be re-applied here, not in the
    # launcher: the key can live in Radnex's own profile, in ~/claude-source,
    # or only in the environment, and only the harness knows how to find all
    # three. The launcher deliberately does not source a profile it cannot find,
    # so without this a session would come back up on the default Logfare
    # endpoint with the wrong credential.
    #
    # Guarded by applies_to_default_endpoint: an endpoint the operator pointed
    # somewhere deliberate — the gateway itself, or any other host — is left
    # exactly as they set it, so a stale selection file cannot hijack it.
    _remembered = sources_mod.current_key()
    for _key, _mod in (("tokenharbour", th_mod), ("openrouter", or_mod),
                       ("unorouter", uno_mod), ("antseed", as_mod),
                       ("aihubmix", ah_mod), ("apinex", api_mod),
                       ("radox", rx_mod)):
        if _remembered == _key and _mod.applies_to_default_endpoint(cfg.base_url):
            _mod.apply_to(cfg)
            break

    # The split is not silent. A stale scope.yaml would otherwise leave the
    # operator believing the guard is armed when nothing is loaded at all —
    # and the old file's meaning cannot be carried over, because an allow-list
    # read as a deny-list would block exactly the hosts that were declared.
    if legacy_scope is not None and legacy_scope.exists():
        print(
            f"radnex: {legacy_scope} is no longer read — the scope guard was "
            "split into two files:\n"
            "  allow.yaml          declared targets; its presence runs tools "
            "unattended\n"
            "  out-of-scope.yaml   hosts that are never touched\n"
            "  Nothing is armed or blocked right now. Rename the file to one of "
            "those to re-enable it.",
            file=sys.stderr,
        )

    if not cfg.workdir.exists():
        print(f"radnex: working directory does not exist: {cfg.workdir}", file=sys.stderr)
        return 2

    if not cfg.api_key_present:
        if sys.stdin.isatty():
            if not _interactive_setup(cfg):
                return 2
        else:
            print(
                "radnex: no credentials found.\n"
                "  Set ANTHROPIC_AUTH_TOKEN (preferred) or ANTHROPIC_API_KEY.\n"
                "  For a free gateway, run `./setup.sh` or configure APInex, Radox AI, OpenRouter.\n"
                "  Or launch interactively with `radnex` to open the setup wizard.",
                file=sys.stderr,
            )
            return 2

    # Launch-time self-update. This runs after the preflight checks, so a
    # launch that cannot proceed anyway never pulls, and before the TUI takes
    # the terminal, so the notice is plain text on a normal screen.
    #
    # An applied update must re-exec rather than continue: radnex.config,
    # radnex.scope and the rest are already imported, and the fast-forward
    # just replaced their files on disk. Running on would be a mix of old and
    # new modules. execv replaces the process image outright, which is exactly
    # what packaging/radnex already does with its own `exec "$PY" -m`.
    #
    # RADNEX_UPDATED guards the loop: once we have re-exec'd, the next launch
    # of main() skips the check entirely, so a flaky fetch cannot make the
    # harness restart itself repeatedly.
    if not os.environ.get("RADNEX_UPDATED"):
        result = update_mod.run(enabled=not args.no_update
                                and os.environ.get("RADNEX_NO_UPDATE") != "1")
        if result.noteworthy:
            update_mod.format_result(result)
        if result.should_reexec:
            os.environ["RADNEX_UPDATED"] = "1"
            # Re-exec through the launcher when there is one, so the venv
            # dependency sync it performs runs against the requirements.txt the
            # update just pulled. Going straight to sys.executable would skip
            # that and boot the new code against the old venv — exactly the
            # case the update flagged. A bare `python -m radnex` has no
            # launcher and re-execs the interpreter, as before.
            launcher = _launcher_path()
            if launcher is not None:
                os.execv(launcher, [launcher, *raw_argv])
            os.execv(sys.executable, [sys.executable, "-m", "radnex", *raw_argv])

    from .ui.app import RadnexApp
    from .termcolors import detect_colors

    # Ask the terminal for its own colours. A terminal draws its padding — the
    # gutter around the text grid — in its own background, and a TUI cannot
    # paint outside the grid, so a hardcoded background leaves a frame of the
    # wrong colour around everything. The same reply carries the foreground and
    # the sixteen ANSI slots, which is what the `system` theme is built from —
    # so this is one round-trip either way, not two.
    #
    # Best-effort throughout: a terminal that does not answer costs one short
    # timeout, the palettes keep their own colours, and `system` falls back to
    # green. term_bg is filtered to a *dark* background because the three fixed
    # palettes are neon-on-black; `system` reads the unfiltered colours, since
    # it takes its text colour from the same place as its background.
    colors = detect_colors()
    app = RadnexApp(cfg, term_bg=colors.dark_bg if colors else None,
                      term_colors=colors)
    # `--resume` (what `/panes` passes to the relaunched process) restores the
    # conversation before the first frame, so the replayed transcript is drawn
    # by the same boot path that draws a fresh one. A bad path is reported and
    # the session starts clean rather than refusing to start at all.
    if args.resume:
        ok, msg = session_mod.load(cfg, app.agent, args.resume)
        if not ok:
            print(f"radnex: {msg} — starting a fresh session", file=sys.stderr)
    result = app.run()
    # `/panes` cannot start tmux itself — tmux has to own the terminal, and the
    # app is holding it — so the command exits with this request and the
    # relaunch happens here, once the terminal is free.
    from . import panes as panes_mod
    if isinstance(result, panes_mod.Relaunch):
        relaunch_argv = _pane_inner_argv(raw_argv)
        resume = ["--resume", result.resume] if result.resume else []
        return main(["--panes", *resume, *relaunch_argv])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
