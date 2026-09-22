#!/usr/bin/env python3
"""Stream a generated bulk file to disk, in chunks, resuming on failure.

    python3 grab.py <file_name.zip> <dest.zip>

`usa.download()` reads the whole response into memory in one call. That works for a 6 MB
agency-year and fails on a 1.1-million-row file: the read times out part way and the bytes
already transferred are thrown away, so a retry starts from zero.

This reads in chunks, writes as it goes, and on a dropped connection reopens and asks for the
rest with a Range header. The connection toll is ~135 s per open, so resuming matters: a
failure two thirds through costs one handshake rather than the whole transfer.

**Range support is checked rather than assumed.** If the server ignores it and replies 200
with the whole file, the partial is discarded and the transfer restarts -- silently appending
a second full copy to a partial one would produce a corrupt zip that still looks plausible.
"""
import http.client, os, ssl, sys, time

HOST = "files.usaspending.gov"
UA = {"User-Agent": "web-snapshots/0.1 (public-record research; +https://github.com/neldivad)",
      "Accept": "*/*"}
CHUNK = 1 << 20


def connect():
    t = time.time()
    c = http.client.HTTPSConnection(HOST, 443, timeout=300,
                                    context=ssl.create_default_context())
    c.connect()
    print(f"  [connected in {time.time()-t:.0f}s]", flush=True)
    return c


def grab(file_name, dest, tries=8):
    part = dest + ".part"
    for attempt in range(tries):
        have = os.path.getsize(part) if os.path.exists(part) else 0
        c = connect()
        h = dict(UA)
        if have:
            h["Range"] = f"bytes={have}-"
        try:
            c.request("GET", f"/generated_downloads/{file_name}", headers=h)
            r = c.getresponse()
            if have and r.status == 200:
                print("  server ignored Range; restarting from zero", flush=True)
                os.remove(part)
                have = 0
            elif have and r.status != 206:
                raise SystemExit(f"  unexpected {r.status} on a Range request")
            total = r.getheader("Content-Length")
            total = (int(total) + have) if total else None
            mode = "ab" if have else "wb"
            t0, got = time.time(), have
            with open(part, mode) as f:
                while True:
                    b = r.read(CHUNK)
                    if not b:
                        break
                    f.write(b)
                    got += len(b)
                    if got % (32 << 20) < CHUNK:
                        pc = f"{got/total:.0%}" if total else "?"
                        print(f"    {got/1e6:>7.0f} MB  {pc:>5}  "
                              f"{got/1e6/max(time.time()-t0,1):.1f} MB/s", flush=True)
            c.close()
            if total and got < total:
                print(f"  short read at {got:,}/{total:,}, retrying", flush=True)
                continue
            os.replace(part, dest)
            print(f"  -> {dest} ({os.path.getsize(dest)/1e6:.0f} MB)", flush=True)
            return dest
        except Exception as e:
            c.close()
            print(f"  {type(e).__name__} after {os.path.getsize(part)/1e6 if os.path.exists(part) else 0:.0f} MB"
                  f", attempt {attempt+1}/{tries}", flush=True)
            time.sleep(4)
    raise SystemExit("  gave up")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    sys.exit(0 if grab(sys.argv[1], sys.argv[2]) else 1)
