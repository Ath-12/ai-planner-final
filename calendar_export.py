"""Turn the day-by-day itinerary into a calendar file (.ics).

Each "Day N" becomes an all-day event with that day's plan as its
description. Works with Google Calendar, Apple Calendar and Outlook.
Standard: RFC 5545 (iCalendar).
"""
from datetime import date, datetime, timedelta, timezone
import re
import uuid

DAY_RE = re.compile(r"^\W*(?:#{1,6}\s*)?\**\s*day\s*(\d{1,2})\b", re.IGNORECASE)


def _plain(md: str) -> str:
    """Markdown -> readable plain text for calendar descriptions."""
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r"\1 (\2)", md)   # keep link targets
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.M)
    return text.replace("**", "").replace("__", "").strip()


def split_days(itinerary_md: str) -> list:
    """Return [(day_number, text), ...] in order. Empty list if no 'Day N' found."""
    days, current = [], None
    for line in itinerary_md.splitlines():
        m = DAY_RE.match(line.strip())
        if m:
            current = [int(m.group(1)), [line]]
            days.append(current)
        elif current is not None:
            current[1].append(line)
    # The same day number can appear twice (e.g. a heading and a bold line): keep the first.
    seen, result = set(), []
    for num, lines in days:
        if num not in seen:
            seen.add(num)
            result.append((num, _plain("\n".join(lines))))
    return result


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace(";", r"\;").replace(",", r"\,").replace("\n", r"\n")


def _fold(line: str) -> str:
    """iCalendar lines must be at most 75 bytes; longer ones continue with a space."""
    out, current = [], b""
    for ch in line:
        b = ch.encode("utf-8")
        if len(current) + len(b) > 74:
            out.append(current.decode("utf-8"))
            current = b" " + b
        else:
            current += b
    out.append(current.decode("utf-8"))
    return "\r\n".join(out)


def build_ics(itinerary_md: str, start: date, destination: str) -> bytes:
    days = split_days(itinerary_md) or [(1, _plain(itinerary_md))]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//NomadSquad//AI Travel Planner//EN",
             "CALSCALE:GREGORIAN", "METHOD:PUBLISH", f"X-WR-CALNAME:{_escape('Trip to ' + destination)}"]
    for num, text in days:
        day = start + timedelta(days=num - 1)
        first_line = next((l for l in text.splitlines() if l.strip()), f"Day {num}")
        summary = re.sub(r"^\W*day\s*\d+\W*", "", first_line, flags=re.I)
        summary = re.sub(r"\s*\(https?://[^)]+\)", "", summary)          # no URLs in titles
        summary = re.split(r"(?<=[.!?])\s|[:;]\s", summary)[0].strip(" .") or "Explore"
        if len(summary) > 60:                                             # cut at a word, not mid-word
            summary = summary[:60].rsplit(" ", 1)[0].rstrip(",") + "…"
        lines += [
            "BEGIN:VEVENT",
            f"UID:{uuid.uuid4()}@nomadsquad",
            f"DTSTAMP:{stamp}",
            f"DTSTART;VALUE=DATE:{day:%Y%m%d}",
            f"DTEND;VALUE=DATE:{day + timedelta(days=1):%Y%m%d}",
            f"SUMMARY:{_escape(f'✈ {destination} · Day {num}: {summary}')}",
            f"LOCATION:{_escape(destination)}",
            f"DESCRIPTION:{_escape(text)}",
            "TRANSP:TRANSPARENT",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return ("\r\n".join(_fold(l) for l in lines) + "\r\n").encode("utf-8")


def next_start_date(month_name: str, today: date | None = None) -> date:
    """Default trip start: the 1st of the chosen travel month, this year or next."""
    today = today or date.today()
    month = datetime.strptime(month_name, "%B").month
    year = today.year if month >= today.month else today.year + 1
    candidate = date(year, month, 1)
    return max(candidate, today)
