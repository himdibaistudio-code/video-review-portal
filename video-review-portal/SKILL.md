---
name: video-review-portal
description: Review a rendered video in a local web page and collect every fix in one pass. Opens the video with a frame strip; the user pauses anywhere, clicks the frame to drop numbered coloured points (red, green, blue, ... as many per frame as needed, each with its own note), adds frames and submits once. Writes REVIEW.md with each frame's time, frame number, every point's colour, position and note, and the frame image with the numbered circles, then Claude fixes ALL issues in one pass and renders once. Use when the user wants to review a video, mark problems on frames, give feedback on a draft or render, or says "open the review portal" / "fix the review".
---

# Video Review Portal

One viewing, every fault pinned to its exact frame, one fix pass, one re-render. Local only: nothing leaves the computer.

## Open a review
1. Find the video to review (the newest render or draft unless the user names one).
2. Start the portal in the background (it keeps running until stopped):
   ```bash
   python3 <this skill folder>/scripts/review_portal.py /path/to/video.mp4
   ```
   Optional: `--words words.json` (word timings `[{"w": "hello", "s": 1.23}, ...]`) and `--script script.txt` (one line per script line)
   so every issue also records what was being said. `--port N` if 8765 is busy (it also moves to the next free port on its own).
   `--no-open` to skip opening the browser.
3. Tell the user the page is open: pause on a problem (or click a thumbnail), click each problem right on the big paused picture (every click
   pops a numbered circle in the next of 10 colours and opens its note box in the right panel), type what is wrong at each pin, "Add frame
   to review", repeat, then "Submit review" once. One entry per frame: going back to a saved frame reopens it for more pins. The edge between
   video and panel drags to resize the panel (wider for vertical Shorts). Wait for them.

## Fix the review ("fix the review")
1. Read the newest `review/<video name>/<timestamp>/REVIEW.md` next to the video, and look at every `issue_NN.png` (the frame with the
   user's numbered coloured circles). Each `point N (colour circle, x %, y %)` line is one fix at that circle.
2. Fix ALL points on ALL frames before rendering anything. Group fixes that touch the same scene. If an issue is unclear, ask about that one only.
3. Render once. Report what changed per frame and point number (e.g. 1.2), with measurements where possible (times, sizes, loudness), not adjectives.
4. Offer the portal again on the new render for the next round.

## Requirements
Python 3 (standard library only) and ffmpeg/ffprobe on the PATH (frame thumbnails and video info).
