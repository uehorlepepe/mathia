# 6. Glossary

This page explains the terms that appear in the project. The definitions are shorter and less formal than a textbook, and they are written for a reader who wants to follow the argument without a mathematics background.

## Parametric curve

A curve written with a third variable, usually time. Instead of writing `y` as a function of `x`, both coordinates are functions of `t`:

```
r(t) = (x(t), y(t))
```

This is useful when the path doubles back on itself, because a simple `y = f(x)` would fail the vertical line test.

## Polynomial

A curve made from powers of a variable, such as:

```
x(t) = a t³ + b t² + c t + d
```

The highest power is the **degree**. A degree 1 polynomial is a line, degree 2 is a parabola, and degree 3 is a cubic. A higher degree can bend more times, but it can also fit noise.

## Degree

The highest power in a polynomial. In this project, the full-track fits use degree 3, and the pull-phase fits use degree 2 for A2 and degree 3 for A3 and Dressel.

## Fit

The process of choosing the coefficients of a model so that the curve stays close to the data. A **good fit** follows the points without adding unnecessary wiggles.

## Residual

The difference between a data point and the model at the same time:

```
residual = observed value - predicted value
```

A residual plot shows whether the model is systematically wrong. A good fit has residuals scattered around zero with no obvious pattern.

## RMSE

Root mean square error. It is a typical distance between the model and the data, in the same units as the data:

```
RMSE = sqrt(mean(residual²))
```

Squaring makes positive and negative residuals count equally, and taking the square root returns the answer to the original units. Lower is better.

In this project there are two RMSEs:

- **Fit RMSE:** the distance between the polynomial and the clicked points, in millimetres.
- **Comparison RMSE:** the distance between two paths, in metres or centimetres.

## R²

The coefficient of determination. It is the fraction of the variation in the data that the model explains:

```
R² = 1 - (sum of squared residuals) / (total sum of squares)
```

- `R² = 1` means a perfect fit.
- `R² = 0` means the model is no better than using the mean.
- `R² < 0` means the model is worse than the mean.

R² can be misleading when the model has the wrong size. That is why the project also reports a **scaled R²**, which fits one overall size factor before computing R².

## BIC

Bayesian Information Criterion. A score for choosing between models. It rewards a good fit but penalises extra terms, so it stops you adding wiggles that do not earn their place. A lower BIC is better.

The project uses BIC as a check on the polynomial degree, but the reported fits use fixed degrees so the comparison is like for like.

## Derivative

The instantaneous rate of change of a function. The derivative of position with respect to time is velocity:

```
v(t) = r'(t) = (x'(t), y'(t))
```

The derivative of the fitted polynomial is computed from its coefficients. It is not a finite difference of the raw clicks, which would amplify click noise.

## Velocity and speed

Velocity is a vector: it has a direction and a size. Speed is the size of the velocity vector:

```
speed(t) = |v(t)| = sqrt(x'(t)² + y'(t)²)
```

In this project, "hand speed" means the speed of the hand in the fixed camera frame, not the swimmer's speed through the pool.

## Arc length

The distance travelled along a curve, not the straight-line distance between the endpoints. For a parametric curve, it is the integral of speed:

```
L = ∫ speed(t) dt
```

The integral is evaluated numerically with Simpson's rule.

## Integral

The area under a curve. In this project, integrating speed over time gives the path length. The integral is a continuous sum: it adds up the small distances travelled in each tiny time interval.

## Calibration

The process of converting pixels to metres. A known length in the image gives the scale:

```
scale = known length / length in pixels
```

The known length here is the swim cap, assumed to be 0.19 m wide.

## Pixel

A single point in a digital image. The video frames are grids of pixels. A click records the pixel coordinates of the hand.

## Scale factor

A single number that enlarges or shrinks one path to match another. In this project, the size factor `k` multiplies Dressel's path to sit on mine.

- `k = 1.128` means Dressel's path is enlarged by 12.8% to match A3.
- `k = 0.538` means Dressel's path is shrunk to 53.8% to match A2.

It is not a body-size measurement. It is a summary of the relative path length in the video.

## Normalised time

Time rescaled to run from 0 to 1 over the interval of interest:

```
u = (t - t_start) / (t_end - t_start)
```

This lets two clips of different durations be compared at the same stage of the movement. A value of `u = 0.5` is halfway through the pull in both clips.

## Uncertainty

A range that shows how much a number could reasonably change if the measurement were repeated or the assumptions were different. The main uncertainty in this project is the cap calibration, about 14% to 18%.

An uncertainty is not a mistake. It is a statement about how precisely the quantity is known.

## Duplicate frame

A frame that repeats the previous picture exactly or almost exactly. Some video files are stored at a high frame rate but contain fewer real pictures. The clicker skips duplicate frames so that each click lands on a new picture.

## Foreshortening

The way an object looks shorter when it is viewed at an angle. The lane ropes are 2.5 m apart, but in these camera views the width is foreshortened, so the rope is not a valid scale. The cap is closer to the hand's plane and is less affected.

## 2D projection

The flat image formed by a camera. A 3D scene is projected onto a 2D sensor, so motion toward or away from the lens is lost. The hand path in this project is a 2D projection.

## Kinematics

The description of motion: position, velocity, acceleration, and path length. Kinematics does not explain the forces that cause the motion. This project is kinematic.

## Pull phase

The part of the stroke from the hand's farthest-forward position, just after entry, to its farthest-back position at the end of the sweep. The recovery is not part of the pull.

## Body-relative path

The hand path measured relative to the swimmer's body, rather than relative to the pool. It removes the swimmer's forward travel and isolates the stroke shape. This project uses the pool frame, not the body frame. A body-relative version is a possible extension.
