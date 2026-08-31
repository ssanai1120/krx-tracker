# -*- coding: utf-8 -*-
"""holdings.json의 종목 시세를 조회해 data/prices.json에 하루치 스냅샷을 추가한다.
GitHub Actions가 평일 장 마감 후 자동 실행하며, 로컬에서 직접 실행해도 된다."""
import json
import sys
import datetime

import FinanceDataReader as fdr

HOLDINGS_FILE = "holdings.json"
PRICES_FILE = "data/prices.json"


BACKFILL_DAYS = 45  # 첫 실행 시 소급할 달력일수 (거래일 약 30일 → 20D% 즉시 표시)


def backfill(holdings, history):
    """기록이 사실상 비어 있으면 과거 일별 종가를 소급해서 채운다."""
    end = datetime.date.today()
    start = end - datetime.timedelta(days=BACKFILL_DAYS)
    by_date = {s["d"]: s["p"] for s in history}
    for h in holdings:
        code, name = h["code"], h["name"]
        try:
            df = fdr.DataReader(code, start, end)
            for ts, row in df.iterrows():
                d = str(ts.date())
                by_date.setdefault(d, {})[code] = float(row["Close"])
            print(f"  {name:<24s} {len(df)}일 소급")
        except Exception as e:
            print(f"  {name:<24s} 소급 실패: {e}")
    return [{"d": d, "p": p} for d, p in sorted(by_date.items())]


def main():
    holdings = json.load(open(HOLDINGS_FILE, encoding="utf-8"))
    try:
        history = json.load(open(PRICES_FILE, encoding="utf-8"))
    except FileNotFoundError:
        history = []

    if len(history) <= 1:  # 최초 실행: 과거 기록 자동 소급
        print("첫 실행 — 과거 시세를 소급해서 채웁니다...")
        history = backfill(holdings, history)

    end = datetime.date.today()
    start = end - datetime.timedelta(days=14)

    snap, day_votes, failed = {}, {}, []
    for h in holdings:
        code, name = h["code"], h["name"]
        try:
            df = fdr.DataReader(code, start, end)
            if df.empty:
                failed.append(name)
                continue
            close = float(df["Close"].iloc[-1])
            day = str(df.index[-1].date())
            snap[code] = close
            day_votes[day] = day_votes.get(day, 0) + 1
            print(f"  {name:<24s} {close:>12,.0f}  ({day})")
        except Exception as e:
            failed.append(name)
            print(f"  {name:<24s} FAIL: {e}")

    if not snap:
        sys.exit("no prices fetched")

    record_day = max(day_votes, key=day_votes.get)  # 대다수 종목의 최신 거래일
    existing = next((s for s in history if s["d"] == record_day), None)
    if existing:
        existing["p"].update(snap)
    else:
        history.append({"d": record_day, "p": snap})
    history.sort(key=lambda s: s["d"])
    history = history[-260:]  # 약 1년치만 유지

    json.dump(history, open(PRICES_FILE, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"\n{record_day} · {len(snap)}종목 기록"
          + (f" · 실패: {', '.join(failed)}" if failed else ""))


if __name__ == "__main__":
    main()
