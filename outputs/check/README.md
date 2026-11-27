# Checks

This folder holds the checks that were run before any curve was fitted. The plots are generated locally and are not committed; the JSON files are committed.

## The files

| File | What it shows |
|---|---|
| `duplicate_frames_a2yifan.json` | A2 has no repeated frames in the tracked window. It is real time. |
| `duplicate_frames_a3yifan.json` | A3 has no repeated frames in the tracked window. It is real time. |
| `duplicate_frames_dressel.json` | Dressel repeats each picture about 3.36 times. Its effective rate is about 17.9 per second, so it is slowed. |
| `lane_rope_check.json` | The lane rope is foreshortened. Using it would imply impossible head widths, so the cap is the scale. |

## Why the checks matter

- **Repeated frames.** If a video repeats each picture, a click on every frame would land on the same picture several times. The clicker skips duplicates, so every click is a new picture. The Dressel clip is slowed, which is why its time and speed are not compared.
- **Lane rope.** The rope is a known 2.5 m, which sounds like a better scale than a cap. In these camera views, however, the rope is at a different depth and is strongly foreshortened. The check shows that using it would make the swimmers' heads 0.39 m to 0.87 m wide, which is impossible. The cap is therefore the working scale.

## The click overlays

The images in this folder (`*_points.png`, `*_cap.jpg`, and so on) are local checks that the clicks landed on the hand and the cap. They are not committed because they are large. They can be regenerated from the source videos with the scripts in `scripts/`.
