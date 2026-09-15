#!/usr/bin/env python3
"""Time to resolution for Australian shortages, estimated from a register that
deletes resolutions after a year.

TGA keeps every CURRENT shortage back to 2003 and every RESOLVED one for about
twelve months. The resolved rows alone say "median 62 days", and that number is the
median of the survivors of a purge that removed every long-running shortage that
ended more than a year ago -- and of a sample that omits the 409 shortages still
running. It is not what a shortage lasts.

The purge window makes a proper estimate possible rather than impossible. Every
shortage that was open at any moment in the last twelve months is on the page:
still-current rows, and resolved rows whose end is within the window. That is a
LEFT-TRUNCATED (a shortage enters observation at the later of its start and the
window start), RIGHT-CENSORED (still running at capture) sample, and Kaplan-Meier
handles both: at each resolution time the risk set is every shortage that had
entered observation and not yet ended.

Shared by chart-3-duration.py, sweep.py and verify.py so the three cannot drift.
"""
import datetime as dt
import sys
sys.path.insert(0, ".")
import shortagelib as S

CAPTURE = dt.date(2026, 9, 10)
WINDOW = 365


def subjects(window_days=WINDOW, capture=CAPTURE):
    """Every shortage observed in the window: t0 = age at entry, t1 = age at exit."""
    w0 = capture - dt.timedelta(days=window_days)
    out = []
    for r in S.tga_records():
        if r.get("status") not in ("C", "R"):          # D never ends; A has not started
            continue
        a = S.tga_date(r.get("shortage_start"))
        b = S.tga_date(r.get("shortage_end")) if r["status"] == "R" else None
        if not a or a > capture:
            continue
        if r["status"] == "R" and (not b or b < w0):
            continue
        entry, exit_ = max(a, w0), (b if r["status"] == "R" else capture)
        if exit_ < entry:
            continue
        out.append({"t0": (entry - a).days, "t1": (exit_ - a).days,
                    "event": r["status"] == "R", "rec": r})
    return out


def km(subs):
    """-> [(t, S(t), at_risk, events, var)], S(0) = 1. Greenwood variance."""
    times = sorted({s["t1"] for s in subs if s["event"]})
    curve, surv, g = [(0, 1.0, 0, 0, 0.0)], 1.0, 0.0
    for t in times:
        risk = sum(1 for s in subs if s["t0"] < t <= s["t1"])
        ev = sum(1 for s in subs if s["event"] and s["t1"] == t)
        if risk and risk > ev:
            surv *= 1 - ev / risk
            g += ev / (risk * (risk - ev))
        elif risk:
            surv = 0.0
        curve.append((t, surv, risk, ev, surv * surv * g))
    return curve


def quantile(curve, p):
    """First time at which S(t) <= p, or None if the curve never gets there."""
    for t, s, *_ in curve:
        if s <= p:
            return t
    return None


def naive_curve(subs):
    """What the resolved rows alone say: share of RESOLVED durations longer than t."""
    d = sorted(s["t1"] for s in subs if s["event"])
    return [(t, sum(1 for x in d if x > t) / len(d)) for t in [0] + d]


def median_of_resolved(subs):
    d = sorted(s["t1"] for s in subs if s["event"])
    return d[len(d) // 2] if d else None
