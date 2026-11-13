# Video Review Portal (free Claude Code skill)

Stop sending feedback one complaint at a time. Watch your video once in a local web page, pause on every problem, click each spot (every click drops a
numbered point in its own colour with its own note), and submit everything at once. Claude gets a REVIEW.md with each frame's time, frame
number, every point's note and a picture of the frame with the numbered circles, fixes all of them in one pass, and renders once.

## Install
Copy the `video-review-portal` folder into `~/.claude/skills/` (all projects) or `<your project>/.claude/skills/` (one project).
Needs Python 3 and ffmpeg. Then ask Claude Code: "open the review portal on out/my_video.mp4". When you have submitted, say "fix the review".

## Run it without Claude
```
python3 scripts/review_portal.py my_video.mp4
```
Your notes land in `review/my_video/<timestamp>/` next to the video (REVIEW.md, review.json, issue_NN.png).

Runs only on your computer (a small local web server on localhost). No account, no upload.

## Which videos
Any video file ffmpeg can read. Tested 2026-11-13: mp4, mov, iPhone HEVC .mov, webm, mkv, 24 and 30 fps, vertical and horizontal.
ProRes / DNxHD and other editing codecs that browsers cannot play get an H.264 preview copy made once (same frame rate, so times and
frame numbers still match the original).

## What can be fixed
The portal collects precise notes: a time, a frame number, numbered pins and what is wrong at each. What Claude can then change depends
on what made the video:
- **Made from a project Claude can edit** (Remotion / three.js / Blender scene, a game engine, an edit timeline): content fixes work.
  "Add a gun to his left hand" at one pinned frame becomes a change in the scene (the prop attached to the hand), so every later frame
  of that shot is right after one re-render.
- **Only a finished clip** (camera footage, a downloaded or AI-generated mp4): edit-level fixes work (cut, trim, speed, colour, crop,
  captions, audio, blur, overlays). Adding or moving things inside a moving shot needs VFX tracking or an AI video tool; the review is
  still the exact brief for whoever does it.
