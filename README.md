# Video Review Portal (free Claude Code skill)

Stop typing timestamps to your AI. Watch your video once in a local web page, **click right on every problem** (each click drops a numbered,
coloured pin with its own note), and submit once. Claude Code gets one `REVIEW.md` with the time, frame number, the words being spoken
and a picture of every pin, fixes everything in one pass, and renders once.

## Install
```bash
git clone https://github.com/himdibaistudio-code/video-review-portal
cp -r video-review-portal/video-review-portal ~/.claude/skills/
```
(or download the zip, unzip it, and put the `video-review-portal` folder into `~/.claude/skills/`)

Needs **Python 3** and **ffmpeg** (`brew install ffmpeg` on a Mac).

## Use
1. In Claude Code: **"open the review portal on out/my_video.mp4"**
2. In the page: pause → click each problem on the picture → type what's wrong at each pin → **Add frame to review** → repeat → **Submit review**
3. Back in Claude Code: **"fix the review"**

Run it without Claude: `python3 video-review-portal/scripts/review_portal.py my_video.mp4`
Notes land in `review/my_video/<timestamp>/` next to the video: `REVIEW.md`, `review.json`, `issue_NN.png`.

## What you get
- Pins on the big paused picture, 10 colours, one note per pin, one entry per frame (go back to a frame to add more pins)
- Frame strip with colour dots, seek bar with ticks, frame-by-frame keys, drag-to-resize panel and strip, A−/A+ text size
- Works on any video: tall or wide, mp4 / mov / webm / mkv; ProRes and other editing codecs get an H.264 preview copy (same frame numbers)
- Runs only on your computer (a small local server); nothing is uploaded

## What can be fixed
The portal collects precise notes. Content fixes (add, move or change things in a shot) work when Claude has the project that made the
video (Remotion, three.js, Blender, a game engine, an edit timeline). For a finished clip with no project, Claude can do edit-level fixes:
cut, trim, speed, colour, crop, captions, audio, blur, overlays.

MIT licence.
