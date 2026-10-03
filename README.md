### Simple telegram bot

Used to control the Arch Linux system.


### Run as a systemd service (start at boot)

Create `/etc/systemd/system/arch-bot.service`:

```ini
[Unit]
Description=Arch Telegram Bot
After=network-online.target
Wants=network-online.target
RequiresMountsFor=/mnt/Misc

[Service]
Type=simple
User=viswa2k
WorkingDirectory=/mnt/Misc/Workspace/Tele_Bots/Arch_Bot
ExecStart=/home/viswa2k/.local/bin/uv run main.py
Restart=on-failure
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

`RequiresMountsFor=/mnt/Misc` makes the service wait for the NTFS drive (mounted with `nofail`) before starting.

`uv run` keeps `.venv` in sync with `pyproject.toml`/`uv.lock` on every start. The project pins Python 3.12 (`.python-version`); if it is missing (e.g. after a Fedora upgrade removes `/usr/bin/python3.12`), install it with uv:

```sh
uv python install 3.12
uv sync
```

### Run manually

The script can be started from any directory:

```sh
uv run --project /mnt/Misc/Workspace/Tele_Bots/Arch_Bot /mnt/Misc/Workspace/Tele_Bots/Arch_Bot/main.py
```

Stop the service first (`sudo systemctl stop arch-bot.service`), otherwise Telegram reports a `Conflict` error because only one instance may poll the bot token.

### Enable the service

Enable and start it:

```sh
sudo systemctl daemon-reload
sudo systemctl enable --now arch-bot.service
```

Check status and logs:

```sh
systemctl status arch-bot.service
journalctl -u arch-bot.service -f
```

If the status shows `203/EXEC`:
- `No such file or directory`: the venv's Python is gone, run `uv python install 3.12 && uv sync`.
- `Permission denied`: SELinux may be blocking it. Check with `sudo ausearch -m avc -ts recent`.
