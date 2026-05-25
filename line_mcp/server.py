"""
LINE Messaging API MCP server.

Reads credentials from environment variables (LINE_CHANNEL_TOKEN, LINE_TARGET_ID)
or falls back to line-config.json in the project root.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    name="LINE Messaging API",
    instructions=(
        "Send LINE messages to a user or group via LINE Messaging API (Push Message). "
        "Tool: send_line_message."
    ),
)

# ── Credential loading ─────────────────────────────────────────────────────────

def _load_config() -> tuple[str | None, str | None]:
    """Return (token, target_id) from env vars or line-config.json."""
    token = os.environ.get("LINE_CHANNEL_TOKEN")
    target = os.environ.get("LINE_TARGET_ID")
    if token:
        return token, target

    cfg_path = Path(__file__).parent.parent / "line-config.json"
    if cfg_path.exists():
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            return cfg.get("LINE_CHANNEL_TOKEN"), cfg.get("LINE_TARGET_ID")
        except Exception:
            pass
    return None, None


# ── Tool ───────────────────────────────────────────────────────────────────────

@mcp.tool()
def send_line_message(message: str, target_id: str | None = None) -> str:
    """Send a text message to a LINE user or group via LINE Messaging API (Push Message).

    Credentials are read from LINE_CHANNEL_TOKEN / LINE_TARGET_ID environment
    variables, or from line-config.json in the project root.

    Args:
        message:   Text to send (supports newlines)
        target_id: Override destination user/group ID.
                   If omitted, uses LINE_TARGET_ID from config.

    Example:
        send_line_message("สวัสดีครับ!")
        send_line_message("ราคาหุ้น CHASE: 0.50 บาท", target_id="C1234...")
    """
    token, default_target = _load_config()
    target = target_id or default_target

    if not token:
        return "❌ ไม่พบ LINE_CHANNEL_TOKEN (ตั้งค่าใน env หรือ line-config.json)"
    if not target:
        return "❌ ไม่พบ LINE_TARGET_ID (ตั้งค่าใน env, line-config.json หรือระบุ target_id)"

    payload = json.dumps({
        "to": target,
        "messages": [{"type": "text", "text": message}],
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.line.me/v2/bot/message/push",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp.read()
        return f"✅ ส่งข้อความ LINE สำเร็จ!\nถึง: {target}\n\n{message}"
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return f"❌ LINE API error {e.code}: {body}"
    except Exception as exc:
        return f"❌ เกิดข้อผิดพลาด: {exc}"


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
