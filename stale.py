"""Flag postings older than a threshold and (optionally) archive them.

Usage:
    python stale.py             # report stale groups; change nothing
    python stale.py --archive   # move stale groups into Archive/
    python stale.py --months 3  # override the 6-month threshold
"""
import argparse
import calendar
import datetime
import shutil
from pathlib import Path

from postings import parse_posting

SCRIPT_DIR = Path(__file__).resolve().parent
POSTINGS_DIR = SCRIPT_DIR / "Postings"
RESUMES_DIR = SCRIPT_DIR / "Customized Resumes"
ARCHIVE_DIR = SCRIPT_DIR / "Archive"


def months_ago(d: datetime.date, n: int) -> datetime.date:
    month_index = d.month - 1 - n
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return datetime.date(year, month, day)


def effective_date(path: Path) -> tuple[datetime.date, str]:
    meta, _ = parse_posting(path.read_text(encoding="utf-8", errors="ignore"))
    ds = meta.get("date_scraped")
    if ds:
        try:
            return datetime.date.fromisoformat(ds), "date_scraped"
        except ValueError:
            pass
    mtime = datetime.date.fromtimestamp(path.stat().st_mtime)
    return mtime, "mtime"


def derived_paths(posting_name: str, resumes_dir: Path) -> list[Path]:
    stem = posting_name[:-4] if posting_name.endswith(".txt") else posting_name
    candidates = [
        resumes_dir / f"summary_{posting_name}",
        resumes_dir / f"Chris Twellman - {stem}.md",
    ]
    return [p for p in candidates if p.exists()]


def find_stale(postings_dir: Path, resumes_dir: Path,
               cutoff: datetime.date, today: datetime.date) -> list[dict]:
    groups = []
    for posting in sorted(postings_dir.glob("*.txt")):
        date, source = effective_date(posting)
        if date < cutoff:
            groups.append({
                "posting": posting,
                "date": date,
                "source": source,
                "age_days": (today - date).days,
                "derived": derived_paths(posting.name, resumes_dir),
            })
    return groups


def archive_group(group: dict, archive_dir: Path) -> list[Path]:
    archive_dir.mkdir(parents=True, exist_ok=True)
    moved = []
    for path in [group["posting"], *group["derived"]]:
        target = archive_dir / path.name
        if target.exists():
            print(f"  skip (already in Archive): {path.name}")
            continue
        shutil.move(str(path), str(target))
        moved.append(target)
    return moved


def _age_label(age_days: int, source: str) -> str:
    return f"{age_days // 30} months (via {source})"


def main() -> None:
    parser = argparse.ArgumentParser(description="Flag postings older than N months.")
    parser.add_argument("--months", type=int, default=6, help="Staleness threshold (default 6)")
    parser.add_argument("--archive", action="store_true", help="Move stale groups into Archive/")
    args = parser.parse_args()

    today = datetime.date.today()
    cutoff = months_ago(today, args.months)
    groups = find_stale(POSTINGS_DIR, RESUMES_DIR, cutoff, today)

    if not groups:
        print(f"No postings older than {args.months} months.")
        return

    print(f"{len(groups)} posting(s) older than {args.months} months:\n")
    for g in groups:
        print(f"- {g['posting'].name}  [{_age_label(g['age_days'], g['source'])}]")
        for d in g["derived"]:
            print(f"    derived: {d.name}")

    if args.archive:
        print("\nArchiving...")
        total = 0
        for g in groups:
            total += len(archive_group(g, ARCHIVE_DIR))
        print(f"Moved {total} file(s) to Archive/.")
    else:
        print("\nRun again with --archive to move these into Archive/.")


if __name__ == "__main__":
    main()
