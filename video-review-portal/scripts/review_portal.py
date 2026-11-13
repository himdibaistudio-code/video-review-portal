#!/usr/bin/env python3
"""Video Review Portal (free skill). A local web page: the video on top, a frame strip below; pause anywhere, click the frame, drop a
coloured numbered point on each problem (as many per frame as you like, each with its own note), add frames, then submit once. Every issue is saved with its exact frame image, so an
AI agent (or a person) can fix ALL of them in one pass instead of one re-render per complaint.

  python3 review_portal.py VIDEO.mp4 [--words words.json] [--script SCRIPT.txt] [--port 8765] [--no-open]
Submit writes <video folder>/review/<YYYYmmdd-HHMMSS>/REVIEW.md + review.json + issue_NN.png (frame + your numbered points).
Optional: --words = [{"w": "word", "s": start_seconds}, ...] (any speech-to-text with word times) shows what was being said at each issue;
--script = plain text, one line per script line, shows the matching line. Local only: nothing leaves your computer. Needs Python 3 + ffmpeg."""
import base64, http.server, json, os, re, subprocess, sys, threading, time, webbrowser
HERE = os.path.dirname(os.path.abspath(__file__))
def opt(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv and sys.argv.index(name) + 1 < len(sys.argv) else default
pos = [a for i, a in enumerate(sys.argv[1:], 1) if not a.startswith("--") and sys.argv[i - 1] not in ("--words", "--script", "--port")]
if not pos or not os.path.exists(pos[0]): sys.exit(__doc__)
VIDEO = os.path.abspath(pos[0]); PORT = int(opt("--port", 8765))
SLUG = os.path.splitext(os.path.basename(VIDEO))[0]
OUT = os.path.join(os.path.dirname(VIDEO), "review", SLUG)
words = json.load(open(opt("--words"))) if opt("--words") else []
script = [l.strip() for l in open(opt("--script")).read().split("\n") if l.strip()] if opt("--script") else []
probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=r_frame_rate:format=duration", "-of", "json", VIDEO], capture_output=True, text=True).stdout
pj = json.loads(probe); num, den = pj["streams"][0]["r_frame_rate"].split("/"); FPS = float(num) / float(den); DUR = float(pj["format"]["duration"])
# thumbnails every 0.5 s (cached per video mtime)
TH = f"{OUT}/thumbs"; STEP = 0.5; stamp = f"{TH}/.src"
key = f"{os.path.abspath(VIDEO)}|{os.path.getmtime(VIDEO)}|h240"   # h240: thumbs 240 px tall (sharp up to the 260 px strip)
if not (os.path.exists(stamp) and open(stamp).read() == key):
    os.makedirs(TH, exist_ok=True)
    for f in os.listdir(TH): os.remove(os.path.join(TH, f)) if f.endswith(".jpg") else None
    print("making thumbnails ...", flush=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VIDEO, "-vf", f"fps={1 / STEP},scale=-2:240", "-q:v", "4", f"{TH}/t%04d.jpg"], check=True)
    open(stamp, "w").write(key)
NTH = len([f for f in os.listdir(TH) if f.endswith(".jpg")])
# browsers play h264 / hevc / vp8 / vp9 / av1; anything else (ProRes, DNxHD, MPEG-2 ...) gets an H.264 preview copy once, same fps,
# so times and frame numbers in the review still match the original file
CODEC = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=codec_name", "-of", "csv=p=0", VIDEO], capture_output=True, text=True).stdout.strip()
PLAY = VIDEO
if CODEC not in ("h264", "hevc", "vp8", "vp9", "av1"):
    PLAY = f"{OUT}/preview_h264.mp4"; pkey = f"{PLAY}.src"
    if not (os.path.exists(PLAY) and os.path.exists(pkey) and open(pkey).read() == key):
        print(f"{CODEC} does not play in browsers: making an H.264 preview copy (once) ...", flush=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VIDEO, "-map", "0:v:0", "-map", "0:a:0?", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                        "-pix_fmt", "yuv420p", "-fps_mode", "passthrough", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", PLAY], check=True)
        open(pkey, "w").write(key)
# script line start times: walk the script lines through the spoken words in order (the page's old word-search guessed L4 at 45 s)
norm = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())
WN = [norm(w["w"]) for w in words]; starts = []; wi = 0
for ln in script:
    toks = [norm(x) for x in ln.split() if norm(x)]
    if not toks: starts.append(starts[-1] if starts else 0); continue
    j = wi
    while j < len(WN) and not (WN[j] == toks[0] and (len(toks) < 2 or j + 1 >= len(WN) or WN[j + 1] == toks[1] or WN[j + 1].startswith(toks[1][:3]))): j += 1
    if j >= len(WN): j = wi
    starts.append(words[j]["s"] if j < len(words) else 0); wi = j + max(1, len(toks) - 2)
INFO = {"lineStarts": starts, "slug": SLUG, "video": os.path.basename(VIDEO), "fps": FPS, "dur": DUR, "step": STEP, "nthumbs": NTH, "words": words, "script": script}
HTML = open(os.path.join(HERE, "review_portal.html")).read()

class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def send(self, code, body, ctype, extra=None):
        self.send_response(code); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(body))); self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items(): self.send_header(k, v)
        try: self.end_headers(); self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError): pass   # the browser cancelled a video range request while seeking: harmless
    def do_GET(self):
        p = self.path.split("?")[0]
        if p in ("/", "/index.html"): return self.send(200, HTML.encode(), "text/html; charset=utf-8")
        if p == "/api/info": return self.send(200, json.dumps(INFO).encode(), "application/json")
        if p.startswith("/thumbs/"):
            f = os.path.join(TH, os.path.basename(p))
            return self.send(200, open(f, "rb").read(), "image/jpeg") if os.path.exists(f) else self.send(404, b"", "text/plain")
        if p == "/video":   # byte ranges, so the browser can seek
            size = os.path.getsize(PLAY); rng = self.headers.get("Range"); a, b = 0, size - 1
            if rng:
                m = re.match(r"bytes=(\d*)-(\d*)", rng); a = int(m.group(1)) if m.group(1) else 0; b = int(m.group(2)) if m.group(2) else size - 1; b = min(b, size - 1)
            with open(PLAY, "rb") as fh: fh.seek(a); data = fh.read(b - a + 1)
            hdr = {"Accept-Ranges": "bytes", "Content-Range": f"bytes {a}-{b}/{size}"}
            ctype = {".webm": "video/webm", ".mov": "video/quicktime", ".mkv": "video/x-matroska"}.get(os.path.splitext(PLAY)[1].lower(), "video/mp4")
            return self.send(206 if rng else 200, data, ctype, hdr)
        self.send(404, b"not found", "text/plain")
    def do_POST(self):
        if self.path != "/api/submit": return self.send(404, b"", "text/plain")
        d = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        stamp_dir = time.strftime("%Y%m%d-%H%M%S"); R = f"{OUT}/{stamp_dir}"; os.makedirs(R, exist_ok=True)
        npts = sum(max(1, len(it.get("marks") or [])) for it in d["issues"])
        md = [f"# Review of {SLUG} ({stamp_dir})", f"Video: {VIDEO} ({DUR:.1f} s, {FPS:g} fps). {len(d['issues'])} frames, {npts} points. Fix ALL of these in one pass, then render once.",
              "Each frame image has numbered coloured circles; the numbered points below say what is wrong at each one.", ""]
        if d.get("general"): md += ["## General notes", d["general"].strip(), ""]
        md.append("## Issues (in film order)")
        for i, it in enumerate(sorted(d["issues"], key=lambda x: x["t"]), 1):
            img = f"issue_{i:02d}.png"; open(f"{R}/{img}", "wb").write(base64.b64decode(it["png"].split(",", 1)[1])); it["image"] = img; del it["png"]
            mks = it.get("marks") or []
            md += [f"### {i}. {it['t']:.2f} s (frame {it['frame']}) · {len(mks) or 'no'} point{'s' if len(mks) != 1 else ''}"]
            if it.get("spoken"): md.append(f"- spoken: \"{it['spoken']}\"")
            if it.get("line"): md.append(f"- script line: {it['line']}")
            md.append(f"- image: {img}")
            for k, m in enumerate(mks, 1): md.append(f"- point {k} ({m['color']} circle, x {m['x']:.0%}, y {m['y']:.0%}): {m['note'].strip()}")
            if it.get("note", "").strip(): md.append(f"- {'frame note' if mks else 'issue'}: {it['note'].strip()}")
            md.append("")
        open(f"{R}/REVIEW.md", "w").write("\n".join(md)); json.dump(d, open(f"{R}/review.json", "w"), indent=1)
        print(f"\nREVIEW SAVED: {R}/REVIEW.md ({len(d['issues'])} frames, {npts} points)", flush=True)
        self.send(200, json.dumps({"ok": True, "path": f"{R}/REVIEW.md", "frames": len(d["issues"]), "points": npts}).encode(), "application/json")

for _try in range(20):   # an older portal still running on the port: use the next free one instead of crashing
    try: srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), H); break
    except OSError: PORT += 1
else: sys.exit("no free port from 8765 to 8784")
url = f"http://localhost:{PORT}"; print(f"review portal for {SLUG}: {url}  (video {VIDEO}, {NTH} thumbnails). Ctrl+C to stop.", flush=True)
if "--no-open" not in sys.argv: threading.Timer(0.6, lambda: webbrowser.open(url)).start()
try: srv.serve_forever()
except KeyboardInterrupt: pass
