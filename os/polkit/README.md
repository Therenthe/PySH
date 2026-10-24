# Appliance network authorization

The PySH backend runs as the dedicated `pysh` account under its systemd user
manager. NetworkManager requests interactive authorization for profile changes
and checkpoints, but that service has no interactive authentication agent. An
active touchscreen session alone does not satisfy these requests.

`50-pysh-networkmanager.rules` grants exactly six NetworkManager actions to that
account:

- `network-control`: activate an explicitly selected connection.
- `wifi.scan`: discover access points.
- `enable-disable-wifi`: control the Wi-Fi radio.
- `settings.modify.own`: manage user-owned saved connections.
- `settings.modify.system`: read saved credentials and update existing system
  connections, including a profile restored by the administrator.
- `checkpoint-rollback`: protect a Wi-Fi change with NetworkManager recovery.

This is an account-level grant, not a Wi-Fi-only D-Bus permission or a grant
limited to one process. The connect adapter validates SSIDs/profile UUIDs and
selects only Wi-Fi devices for activation and checkpoints. The local API retains
its loopback, Origin and session-token checks. Processes running as `pysh` share
the six permissions; the account must remain dedicated to the appliance.

The rule grants nothing to other users or action names. It adds no group/sudo
membership and grants no hostname, global DNS, global networking shutdown or
NetworkManager reload action. Other system policies continue to apply.

The image hook installs the rule as `root:root`, mode `0644`, in
`/etc/polkit-1/rules.d/`. Polkit watches that directory; installing the rule does
not require restarting NetworkManager or disconnecting a network. Existing
devices require a separately reviewed installation with a verified backup;
adding this source file does not modify a running appliance.

Run `node --test tests/networkmanager-policy.test.mjs` to evaluate the actual
rule's grants and exclusions. These tests do not establish hardware acceptance.
