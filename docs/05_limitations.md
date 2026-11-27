# 5. Limitations

A good mathematical model is useful partly because it says what it cannot do. This page lists the main limits of the study and explains what each one means for the conclusion.

## 1. The video is a 2D projection of a 3D motion

A single camera records a flat image. If the hand moves toward or away from the lens, that motion is invisible. The recorded path is the **shadow** of the real 3D path on the image plane.

**What this means:** the comparison is valid for the part of the motion that stays in the camera plane. It cannot capture depth, and it cannot tell us whether the hand is sweeping under the body or out to the side.

**What would help:** a second camera at a different angle, or a calibrated stereo pair, would allow a 3D reconstruction. That is well beyond the scope of this IA.

## 2. The calibration is uncertain by about 15%

The scale comes from the swim cap. The cap is small in the frame, and the assumed cap width of 0.19 m is a population average, not a measurement of the two swimmers. The relative uncertainty is 18.1% for A2, 15.3% for A3, and 14.1% for Dressel.

**What this means:** every length and speed has a 14% to 18% scale uncertainty. A 1.76 m path could be 1.49 m or 2.03 m if the scale is at the edge of its range. The 16.5 cm A3 against Dressel RMSE is smaller than this uncertainty, so the absolute gap should not be read as a precise physical distance.

**What would help:** a calibration object at the same depth as the hand, such as a measured board held beside the swimmer, would reduce the uncertainty. A cap width measured on the swimmer, rather than assumed, would also help.

## 3. The camera frame includes the swimmer's forward travel

The camera is fixed, so the coordinates are in the pool frame. The hand path therefore includes the swimmer's translation through the water. This is the path the hand actually traces through the water, which is a meaningful physical quantity. It is not the same as the hand's path relative to the torso.

**What this means:** a swimmer who travels farther during the same pull will have a longer pool-frame path even if the arm motion is identical. The comparison mixes the arm sweep with the body's forward motion.

**What would help:** subtracting a body landmark, such as the hip or the cap, would give a body-relative path. That isolates the stroke shape. The repository includes a development script for this (`scripts/development/body_relative.py`), but the final results use the pool frame. A body-relative version would be a natural extension.

## 4. The elite footage is slowed

The Dressel clip is stored at 60 fps, but in the tracked window each real picture is repeated about 3.36 times. The effective picture rate is about 17.9 per second, not 60. The time stamps in the CSV are nominal, not physical.

**What this means:** the shape and the arc length are still usable, because they are spatial quantities. The absolute time and the absolute speed are not. This is why the README does not compare speed with Dressel.

**What would help:** a copy of the clip at its original frame rate, or the original broadcast footage, would allow a time comparison.

## 5. A2's pull is very short

A2's pull has 9 points over 0.267 s. That is enough for a quadratic and a rough length, but not enough for a confident cubic. The full-track A2 fit is also the weakest, with R² 0.8275.

**What this means:** the A2 result is **indicative**, not a fair second trial. Its lower shape score is partly a real difference and partly the short window. The README says this explicitly.

**What would help:** a longer A2 clip, or a re-digitisation that captures the full pull, would make the A2 comparison stronger.

## 6. There is one pull per clip

Each clip contains one tracked pull. There are no repeat trials, so the study cannot separate a real technique difference from frame-to-frame variation or a single bad click.

**What this means:** the numbers describe these three clips, not the swimmers in general. A second pull from the same clip would give an idea of the repeatability. Several pulls would give a distribution.

**What would help:** digitise two or three pulls from each swimmer and report the spread.

## 7. The manual clicks have their own error

The hand was clicked by hand. The clicker shows a magnified view, and the points were checked against the frames, but there is no independent repeat digitisation. A click error of a few pixels becomes a few millimetres to a centimetre after calibration.

**What this means:** the click error is probably smaller than the calibration error, but it is not measured. The fit RMSE of 26 mm to 37 mm includes both the click scatter and any real departure from a polynomial.

**What would help:** digitise the same clip twice, independently, and compare the two sets of points. That would give a direct estimate of click repeatability.

## 8. The polynomial is a smoothing tool, not a physical law

A cubic can fit a smooth path, but it is not derived from biomechanics. A different degree, or a different window, would change the coefficients, the speed, and the arc length slightly.

**What this means:** the R² values show that the polynomial fits the points well, not that the hand follows a polynomial law. The derivatives and the arc length are estimates from the fitted curve.

**What would help:** compare a polynomial with a spline or a physical model, and report how much the arc length changes. The current script can vary the degree; a sensitivity table would make the effect visible.

## 9. The study measures motion, not force or efficiency

A longer or faster hand path does not prove more propulsion. The hand could be slipping through the water, or the body could be in a better streamline. The IA measures kinematics. It does not measure force, drag, pressure, or the swimmer's speed.

**What this means:** the results should not be read as "A3 is a better swimmer than A2" or "Dressel's technique is better". They describe how the hand paths differ in these clips.

**What would help:** force sensors, pressure sensors, or a velocity measurement of the body would connect the hand motion to propulsion. That is a different project.

## 10. The clips are not a controlled experiment

The three clips come from different pools, cameras, distances, angles, and possibly different training or race contexts. The elite clip is a race; my clips are training. The lighting and the water clarity differ.

**What this means:** the comparison is **illustrative**. It shows what the method can measure, not a fair race between two swimmers.

**What would help:** film all three swimmers with the same camera, at the same distance and angle, in the same session. That is not possible for an Olympic clip, but it is possible for a comparison between training partners.

## Summary

| Limit | Effect on the conclusion | Severity |
|---|---|---|
| 2D projection | depth motion is invisible | fundamental |
| cap calibration, about 15% | absolute lengths are uncertain | large |
| pool-frame path | includes forward travel | moderate to large |
| slowed elite footage | speed is not comparable | large for speed, none for shape |
| A2 short window | A2 result is indicative | large for A2 |
| one pull per clip | no repeatability estimate | moderate |
| manual clicks | small extra scatter | small to moderate |
| polynomial choice | small changes in speed and length | small to moderate |
| kinematics only | no force or efficiency claim | fundamental |
| different conditions | comparison is illustrative | fundamental |

The next page is a glossary of the terms used in the project.
