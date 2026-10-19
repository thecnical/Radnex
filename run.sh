#!/usr/bin/env bash
# run.sh — run Radnex straight from the checkout.
#
# The real launcher lives in packaging/; it needs RADNEX_ROOT to point at the
# checkout (its own directory is packaging/). This shim does exactly that, so
# `./run.sh` starts the proxy and the harness for you. The launcher then uses
# the checkout's own venv (./.venv) when it exists, so there is nothing to
# activate:
#
#   python3 -m venv .venv && pip install -r requirements.txt
#   ./setup.sh                          # verify the route end-to-end
#   ./run.sh                            # launch
#
# If you installed with install.sh, a `radnex` command is already on your PATH
# and this shim is not needed.

set -euo pipefail

_self_dir="$(cd -- "$(dirname -- "$(readlink -f -- "${BASH_SOURCE[0]}")")" && pwd -P)"
export RADNEX_ROOT="$_self_dir"
exec "$_self_dir/packaging/radnex" "$@"
