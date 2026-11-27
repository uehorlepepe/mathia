# 1. The question and the aim

## The question

> **When my hand sweeps through the water in a 50 m freestyle sprint, what path does it trace, and how does that path compare with the same phase swum by an elite sprinter, Caeleb Dressel?**

The question is deliberately narrow. It looks at **one phase of one stroke, one hand, and two swimmers**. It does not try to model swimming in general, and it does not try to explain every part of the race.

The phase is the **underwater hand pull**: from the moment the hand is farthest forward, just after entry, to the moment it is farthest back at the end of the sweep. The recovery, the turn, the dive, and the finish are outside the scope.

## Why this question

I am a competitive high school swimmer. I placed second in the B final at OFSAA and I have coaching experience. In training, most stroke feedback is qualitative. A coach says "catch the water", "finish the pull", or "hold the pressure". These are useful cues, but they are not numbers.

A hand moving through water traces a curve. That curve can be written as a vector function, differentiated to get velocity, integrated to get path length, and compared with another swimmer's curve. The mathematical step is to turn a coaching cue into a parametric curve and a disagreement between two swimmers into a residual with an uncertainty attached.

That is what interests me: the same stroke can be described in two ways, one in words and one in calculus, and the second one can be checked.

## The aim

The aim is to:

1. Fit a parametric polynomial model `r(t) = (x(t), y(t))` to my hand path and to Dressel's hand path.
2. Compute the hand speed and the arc length of each path with calculus.
3. Quantify how far my path departs from Dressel's using a distance in metres, RMSE, and R².
4. Report the size difference between the two paths as an explicit scale factor, rather than hiding it inside a scale-free score.
5. Propagate the calibration uncertainty into every length and speed.

## What success looks like

The exploration succeeds if it produces:

- **A convergent model.** A parametric fit with R² at least 0.95 in the pull window, and residuals with no obvious trend.
- **A computed path length and speed.** Each value carries an uncertainty from the calibration.
- **A quantified difference.** A distance in metres between my path and Dressel's, and a shape score after allowing for size.
- **An honest account of scale.** The size difference is reported as a number, not absorbed into the comparison.
- **A clear statement of limits.** The reader can see what the camera, the calibration, and the sample size do and do not support.

## What this is not

This is not a controlled experiment. The three clips were filmed at different pools, with different cameras, at different distances, and possibly at different points in a race or training session. The elite clip is a broadcast clip that has been slowed down. The comparison is therefore **illustrative**, not a fair race between two swimmers.

It is also not a study of force or efficiency. A longer hand path is not automatically a better hand path. The IA measures motion. It does not measure propulsion, drag, or the force the water exerts on the hand.

Those limits are not a weakness of the question. They are the reason the question has to be answered with an explicit method and an explicit uncertainty, rather than with an opinion.

## The personal engagement

The project started with a simple observation: two swimmers can look completely different underwater even when their race times are close. The usual explanation is "technique", but that word does not say what is different or by how much.

I chose the hand path because it is the part of the stroke I can see most clearly in a side-on video, and because it is the part a coach talks about most often. The mathematical work is to make that conversation measurable.

The next page describes the data: the three clips, the manual clicks, the calibration, and the checks that were run before any curve was fitted.
