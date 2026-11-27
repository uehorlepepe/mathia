# 3. The method

This page explains the mathematics in the order it was used. Each step is also implemented in a script, but the script is not needed to follow the argument.

## Step 1: choose the phase

The hand path has several parts: entry, pull, exit, recovery, and re-entry. Comparing the whole cycle would mix different physical actions. I therefore restrict the comparison to the **pull phase**.

The pull starts at the frame where the hand is farthest forward, just after entry. It ends at the frame where the hand is farthest back, at the end of the backward sweep. In the coordinates, the hand starts at `x = 0` and moves to negative `x`, so:

```
entry = frame of maximum x
exit  = frame of minimum x after entry
```

Frames after the exit are recovery and are dropped. This gives the same physical phase in all three clips.

The pull windows are:

| Clip | Frames | Points | Duration |
|---|---|---|---|
| A2 | 320 to 328 | 9 | 0.267 s |
| A3 | 177 to 194 | 18 | 0.567 s |
| Dressel | 682 to 778 | 13 | 1.600 s (nominal, slowed footage) |

The full-track fits use every digitised frame, including recovery. They are reported as a check, but the headline comparison uses the pull phase.

## Step 2: write the path as a parametric curve

A path in two dimensions can be written as a vector function of time:

```
r(t) = (x(t), y(t))
```

`x(t)` is the forward position at time `t`, and `y(t)` is the vertical position. Writing the path this way is useful because the two coordinates can be fitted separately, and because the derivative and the integral have direct physical meanings.

The coordinates come from the manual clicks:

```
x(t) = (x_pixel(t) - x_pixel(0)) * scale
y(t) = -(y_pixel(t) - y_pixel(0)) * scale
```

The scale is the cap calibration from [02_data.md](02_data.md). The minus sign makes upward positive.

**Important:** the camera is fixed in all three clips, so the coordinates are in the **pool frame**, not the body frame. The path therefore includes the swimmer's forward travel through the water. This is the path the hand actually traces through the water, which is a meaningful physical quantity. It is not the same as the hand's path relative to the torso. A body-relative version would subtract the swimmer's translation and isolate the stroke shape. That is a possible extension, not part of this IA.

## Step 3: fit a polynomial

Each coordinate is fitted with a polynomial in time:

```
x(t) = a_n t^n + a_(n-1) t^(n-1) + ... + a_1 t + a_0
y(t) = b_n t^n + b_(n-1) t^(n-1) + ... + b_1 t + b_0
```

A polynomial is a smooth curve made from powers of `t`. It is a reasonable choice here because the hand path is smooth and the data are short. It is not a physical law. It is an interpolation and smoothing tool.

### Choosing the degree

The degree is the highest power in the polynomial. A higher degree can follow more wiggles, but it can also fit noise and produce unrealistic derivatives.

The final fits use:

- **Full track:** degree 3 for all three clips, so the comparison is like for like.
- **Pull phase:** degree 2 for A2, because 9 points cannot support a confident cubic. Degree 3 for A3 and Dressel.

The code can also choose the degree automatically with the **Bayesian Information Criterion (BIC)**. BIC rewards a good fit but penalises extra terms. It is a check on the choice, not the final rule. The reported results use the fixed degrees above so that no clip gets an unfair flexibility advantage.

### Fit quality

Two numbers describe the fit:

```
R² = 1 - (sum of squared residuals) / (total sum of squares)
RMSE = sqrt(mean(residual²))
```

- **R²** is the fraction of the variation in the data explained by the model. 1 is a perfect fit, 0 is no better than using the mean, and a negative value means the model is worse than the mean.
- **RMSE** is a typical distance between the model and the data, in the same units as the data. Lower is better.

The pull-phase fits have R² between 0.989 and 0.995 and residual RMSE between 26 mm and 37 mm. That is small compared with the path lengths of 0.76 m to 1.76 m.

## Step 4: differentiate to get velocity and speed

The derivative of position with respect to time is velocity:

```
v(t) = r'(t) = (x'(t), y'(t))
```

The speed is the magnitude of the velocity vector:

```
speed(t) = |v(t)| = sqrt(x'(t)² + y'(t)²)
```

The derivatives are computed analytically from the fitted polynomial coefficients, not by differencing the raw points. This is why the fitted curve is useful: differentiating raw clicks would amplify the click noise.

The mean speed is the path length divided by the duration. The peak speed is the maximum of `speed(t)` over the fitted interval. The peak is more sensitive to the fit than the mean, so it is reported with a caution.

## Step 5: integrate to get arc length

The length of a curve is the integral of speed:

```
L = ∫ from t_start to t_end of sqrt(x'(t)² + y'(t)²) dt
```

This is the distance the hand actually travels along its curved path, not the straight-line distance between the start and the end. It is computed numerically with Simpson's rule on a fine grid.

For the pull phase:

| Clip | Arc length | Uncertainty |
|---|---|---|
| A2 | 0.762 m | ± 0.138 m |
| A3 | 1.764 m | ± 0.270 m |
| Dressel | 1.418 m | ± 0.199 m |

The uncertainty is propagated from the scale:

```
ΔL ≈ L * (Δscale / scale)
```

If the scale is 15% too small, every length is 15% too small. This is a first-order approximation, which is appropriate for a 15% uncertainty.

## Step 6: compare the paths

The two paths may have different durations and different numbers of points. To compare their **shape**, I put both on a common normalised time:

```
u = (t - t_start) / (t_end - t_start)
```

`u` runs from 0 to 1 for every clip. I then evaluate both paths at the same 300 values of `u`, align them at the start, and compute the distance at each `u`:

```
d(u) = sqrt( (x_1(u) - x_2(u))² + (y_1(u) - y_2(u))² )
```

The typical gap is the root mean square of these distances:

```
RMSE = sqrt( mean( d(u)² ) )
```

This is the number reported in centimetres. It has the same units as the coordinates.

### The scale factor

A raw RMSE mixes two things: a difference in **shape** and a difference in **size**. A path can have the right shape but be 20% larger, and the raw RMSE will call that a disagreement.

To separate the two, I fit one overall scale factor `k` that minimises the distance between Dressel's path and mine:

```
minimise over k:  sum( |k * p_Dressel(u) - p_mine(u)|² )
```

The value of `k` that solves this is:

```
k = (p_Dressel · p_mine) / (p_Dressel · p_Dressel)
```

`k` is a single number that enlarges or shrinks one path to match the other. It is **not** a claim about body size. It is a summary of how much larger one path is than the other in the video.

The **shape score** is the R² of Dressel's model on my points after this one scale factor is allowed. It removes overall size and asks whether the curves have the same shape. The raw R² is also reported, but it is not the headline because it penalises size.

### The rotation check

As a robustness check, I also allow one rotation as well as one scale. This asks a slightly different question: if the two cameras were at slightly different angles, would the shapes agree? The rotation angle and the rotated R² are reported in [04_results.md](04_results.md). They are a check, not the main result.

## Step 7: report the uncertainty

Every length and speed carries the calibration uncertainty. The comparison numbers also carry it, but in a more complicated way: the RMSE depends on both paths, so a scale error in either clip moves the number.

A useful rule of thumb is:

- A 15% scale error on a 1.7 m path is about 0.26 m.
- The A3 versus Dressel RMSE is 0.165 m, which is **smaller** than the scale uncertainty on either path.
- Therefore the 16 cm gap should be read as "about 16 cm in this calibration", not as a definitive physical distance.
- The shape score is more robust because it removes one overall scale factor. It is the better number for comparing shape.

This is why the README leads with both numbers and explains which one to trust for which question.

## Summary of the method

| Step | Mathematics | Output |
|---|---|---|
| 1 | choose entry and exit frames | a common phase |
| 2 | convert pixels to metres | `(x(t), y(t))` |
| 3 | fit polynomials | `x(t)`, `y(t)`, R², RMSE |
| 4 | differentiate | velocity and speed |
| 5 | integrate speed | arc length |
| 6 | normalise time and align | RMSE and scale factor |
| 7 | propagate scale uncertainty | uncertainty on every length |

The next page gives the full results.
