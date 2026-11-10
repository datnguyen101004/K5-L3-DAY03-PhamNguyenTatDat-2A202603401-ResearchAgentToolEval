from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from tools._shared import ROOT, err


def save_markdown_report(filename: str = "", content: str = "", title: str = "") -> dict[str, Any]:
    """Xuất câu trả lời hoặc báo cáo nghiên cứu ra file Markdown (.md) cục bộ."""
    try:
        content_str = (content or "").strip()
        if not content_str:
            return {
                "tool": "export_md",
                "status": "error",
                "message": "Nội dung xuất (content) không được để trống.",
            }

        # Sanitize filename
        clean_name = (filename or "").strip()
        if not clean_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            clean_name = f"report_{timestamp}.md"
        else:
            # Bỏ ký tự không hợp lệ và ngăn directory traversal
            clean_name = re.sub(r'[\\/*?:"<>|]', "_", clean_name)
            clean_name = Path(clean_name).name
            if not clean_name.lower().endswith(".md"):
                clean_name = f"{clean_name}.md"

        reports_dir = ROOT / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        file_path = reports_dir / clean_name

        # Định dạng văn bản với title nếu có
        lines = []
        if title and title.strip():
            lines.append(f"# {title.strip()}\n")
        lines.append(content_str)
        final_text = "\n".join(lines) + "\n"

        # Write the exact UTF-8 bytes on every OS (no Windows CRLF translation).
        encoded_text = final_text.encode("utf-8")
        file_path.write_bytes(encoded_text)

        return {
            "tool": "export_md",
            "status": "success",
            "filename": clean_name,
            "file_path": str(file_path),
            "bytes_written": len(encoded_text),
        }
    except Exception as exc:
        return err("export_md", exc)

