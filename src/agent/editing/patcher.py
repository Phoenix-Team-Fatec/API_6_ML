from pathlib import Path
from difflib import unified_diff


def apply_full_file_update(target_file: str, updated_code: str, dry_run: bool = True) -> str:
    path = Path(target_file)
    old_code = path.read_text(encoding="utf-8")

    if not dry_run:
        path.write_text(updated_code, encoding="utf-8")

    diff = "\n".join(
        unified_diff(
            old_code.splitlines(),
            updated_code.splitlines(),
            fromfile=f"{target_file} (old)",
            tofile=f"{target_file} (new)",
            lineterm="",
        )
    )
    return diff