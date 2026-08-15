#!/usr/bin/env python3

import argparse
import json
import math
import os
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape


WIDTH = 960
HEIGHT = 520
LEFT = 78
RIGHT = 38
TOP = 116
BOTTOM = 78
PLOT_WIDTH = WIDTH - LEFT - RIGHT
PLOT_HEIGHT = HEIGHT - TOP - BOTTOM


def fetch_star_dates(repository: str, token: str) -> list[date]:
    dates: list[date] = []
    page = 1
    while True:
        request = Request(
            f"https://api.github.com/repos/{repository}/stargazers?per_page=100&page={page}",
            headers={
                "Accept": "application/vnd.github.star+json",
                "Authorization": f"Bearer {token}",
                "User-Agent": "star-history-generator",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        with urlopen(request, timeout=30) as response:
            batch = json.load(response)
        dates.extend(
            datetime.fromisoformat(item["starred_at"].replace("Z", "+00:00"))
            .astimezone(timezone.utc)
            .date()
            for item in batch
        )
        if len(batch) < 100:
            return sorted(dates)
        page += 1


def nice_y_axis(total: int) -> tuple[int, int]:
    if total == 0:
        return 5, 1
    rough_step = max(total / 4, 1)
    magnitude = 10 ** math.floor(math.log10(rough_step))
    normalized = rough_step / magnitude
    step_factor = 1 if normalized <= 1 else 2 if normalized <= 2 else 5 if normalized <= 5 else 10
    step = int(step_factor * magnitude)
    return math.ceil(total / step) * step, step


def render_svg(repository: str, dates: list[date]) -> str:
    today = date.today()
    current_horizon = (today.replace(day=1) + timedelta(days=32)).replace(day=1)
    if dates:
        start = dates[0] - timedelta(days=7)
        end = max(dates[-1] + timedelta(days=7), current_horizon)
    else:
        end = current_horizon
        start = end - timedelta(days=30)

    span = max((end - start).days, 1)
    total = len(dates)
    y_max, y_step = nice_y_axis(total)

    def x(day: date) -> float:
        return LEFT + ((day - start).days / span) * PLOT_WIDTH

    def y(value: int) -> float:
        return TOP + PLOT_HEIGHT - (value / y_max) * PLOT_HEIGHT

    counts = Counter(dates)
    cumulative = 0
    path_parts = [f"M {x(start):.2f} {y(0):.2f}"]
    for day in sorted(counts):
        cumulative += counts[day]
        path_parts.extend([f"H {x(day):.2f}", f"V {y(cumulative):.2f}"])
    path_parts.append(f"H {x(end):.2f}")
    line_path = " ".join(path_parts)
    area_path = f"{line_path} V {y(0):.2f} H {x(start):.2f} Z"

    y_grid = []
    for value in range(0, y_max + 1, y_step):
        position = y(value)
        y_grid.append(
            f'<line x1="{LEFT}" y1="{position:.2f}" x2="{WIDTH - RIGHT}" y2="{position:.2f}" class="grid" />'
            f'<text x="{LEFT - 14}" y="{position + 5:.2f}" class="axis" text-anchor="end">{value}</text>'
        )

    tick_dates = [start]
    for year in range(start.year + 1, end.year + 1):
        annual_tick = date(year, 1, 1)
        if x(annual_tick) - x(tick_dates[-1]) >= 72 and x(end) - x(annual_tick) >= 72:
            tick_dates.append(annual_tick)
    tick_dates.append(end)
    x_grid = []
    for index, day in enumerate(tick_dates):
        position = x(day)
        if index not in (0, len(tick_dates) - 1):
            x_grid.append(
                f'<line x1="{position:.2f}" y1="{TOP}" x2="{position:.2f}" y2="{TOP + PLOT_HEIGHT}" class="grid vertical" />'
            )
        label = day.strftime("%b %Y") if index in (0, len(tick_dates) - 1) else str(day.year)
        anchor = "start" if index == 0 else "end" if index == len(tick_dates) - 1 else "middle"
        x_grid.append(
            f'<text x="{position:.2f}" y="{TOP + PLOT_HEIGHT + 32}" class="axis" text-anchor="{anchor}">{label}</text>'
        )

    last_date = dates[-1] if dates else end
    safe_repository = escape(repository)
    subtitle = f"{total} stars" if total != 1 else "1 star"

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="960" height="520" viewBox="0 0 960 520" role="img" aria-labelledby="title description">
  <title id="title">Star history for {safe_repository}</title>
  <desc id="description">Cumulative GitHub stars over time. Current total: {total}.</desc>
  <defs>
    <linearGradient id="background" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#111827" />
      <stop offset="1" stop-color="#080d16" />
    </linearGradient>
    <linearGradient id="area" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#22d3ee" stop-opacity="0.42" />
      <stop offset="1" stop-color="#22d3ee" stop-opacity="0.02" />
    </linearGradient>
    <linearGradient id="line" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#38bdf8" />
      <stop offset="1" stop-color="#a3e635" />
    </linearGradient>
    <filter id="glow" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="4" result="blur" />
      <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
    </filter>
    <style>
      text {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
      .grid {{ stroke: #334155; stroke-width: 1; opacity: .55; }}
      .grid.vertical {{ opacity: .28; stroke-dasharray: 4 7; }}
      .axis {{ fill: #94a3b8; font-size: 13px; }}
    </style>
  </defs>
  <rect width="960" height="520" rx="22" fill="url(#background)" />
  <rect x="1" y="1" width="958" height="518" rx="21" fill="none" stroke="#334155" stroke-opacity=".65" />
  <text x="52" y="57" fill="#f8fafc" font-size="28" font-weight="700">Star History</text>
  <text x="52" y="87" fill="#94a3b8" font-size="16">{safe_repository}</text>
  <text x="730" y="61" fill="#a3e635" font-size="26" font-weight="700">★ {subtitle}</text>
  {''.join(y_grid)}
  {''.join(x_grid)}
  <path d="{area_path}" fill="url(#area)" />
  <path d="{line_path}" fill="none" stroke="url(#line)" stroke-width="4" stroke-linejoin="round" filter="url(#glow)" />
  <circle cx="{x(last_date):.2f}" cy="{y(total):.2f}" r="6" fill="#a3e635" stroke="#f8fafc" stroke-width="2" />
  <text x="52" y="506" fill="#64748b" font-size="12">Generated from GitHub stargazer timestamps</text>
</svg>
'''


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an SVG chart of GitHub star history.")
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY"))
    parser.add_argument("--output", default="assets/star-history.svg")
    args = parser.parse_args()

    if not args.repo:
        parser.error("--repo or GITHUB_REPOSITORY is required")
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        parser.error("GITHUB_TOKEN is required")

    svg = render_svg(args.repo, fetch_star_dates(args.repo, token))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    main()
