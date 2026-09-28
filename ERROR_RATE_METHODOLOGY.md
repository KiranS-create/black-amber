# AegisTrace — Empirical Error Rate & Statistical Uncertainty Methodology

## 1. Mathematical Foundations of Forensic Error Rate Estimation

In forensic evidence evaluation, claims of zero error or $100\%$ accuracy without sample size context and uncertainty intervals are legally inadmissible and scientifically invalid. AegisTrace adheres to the **National Commission on Forensic Science (NCFS)** and **ISO/IEC 17025** guidelines regarding the reporting of forensic error rates and uncertainty bounds.

### Categorization of Decision Space:
Given an inquiry regarding a leaked document carrier artifact $A$:
- **True Positive ($TP$)**: Carrier $A$ originates from recipient $R_i$, and the system attributes $A$ to $R_i$.
- **True Negative ($TN$)**: Carrier $A$ is an unwatermarked negative, tampered artifact, or foreign release, and the system correctly abstains (`NO_SIGNAL`, `INSUFFICIENT_EVIDENCE`, or `CONFLICT`).
- **False Positive ($FP$)**: Carrier $A$ is attributed to $R_j$ when $A$ was actually released to $R_i$ ($i \neq j$), or $A$ is attributed to $R_j$ when $A$ is a clean negative carrier. **In forensic attribution, False Positives represent false accusations and have an infinite penalty.**
- **False Negative ($FN$)**: Carrier $A$ originates from $R_i$, but the system abstains or reports `NO_SIGNAL`. In a fail-closed system, false negatives are safe failures (unsolved leak rather than wrongful conviction).

---

## 2. Statistical Uncertainty Interval Formulations

When observing $k$ occurrences in $n$ independent Bernoulli trials (such as $k = 0$ false positives out of $n = 200$ negative tests), the sample point estimate $\hat{p} = \frac{k}{n}$ is accompanied by standard confidence intervals.

### A. Wilson Score Interval (Recommended for Moderate-to-Large $n$)
The Wilson score interval provides superior coverage near the boundaries ($k = 0$ or $k = n$) compared to the Wald normal approximation:

$$p \in \frac{\hat{p} + \frac{z^2}{2n} \pm z \sqrt{\frac{\hat{p}(1 - \hat{p})}{n} + \frac{z^2}{4n^2}}}{1 + \frac{z^2}{n}}$$

For a $95\%$ two-sided confidence interval ($\alpha = 0.05$), $z = 1.95996$.

When $k = 0$ ($\hat{p} = 0$):

$$p \in \left[0, \frac{\frac{z^2}{n}}{1 + \frac{z^2}{n}}\right] = \left[0, \frac{3.8415}{n + 3.8415}\right]$$

For $n = 200$, the $95\%$ Wilson upper bound is:

$$p_{\text{upper}} = \frac{3.8415}{203.8415} = 0.018845 \quad (1.88\%)$$

---

### B. Clopper-Pearson Exact Binomial Interval (Conservative Legal Standard)
The Clopper-Pearson interval is derived from the exact binomial distribution by inverting the regularized incomplete beta function $I_x(a, b)$:

- **Lower Bound ($k > 0$)**: $I_{\text{lower}}(k, n - k + 1) = \frac{\alpha}{2}$
- **Upper Bound ($k < n$)**: $I_{\text{upper}}(k + 1, n - k) = 1 - \frac{\alpha}{2}$

For $k = 0$:
- $\text{Lower Bound} = 0$
- $\text{Upper Bound} = 1 - \left(\frac{\alpha}{2}\right)^{1/n} = 1 - (0.025)^{1/n}$

For $n = 200$:

$$p_{\text{upper}} = 1 - (0.025)^{1/200} = 1 - 0.981725 = 0.018275 \quad (1.83\%)$$

---

### C. Rule of Three for Zero Observed Events
For quick preliminary estimates when $k = 0$:

$$\text{Upper } 95\% \text{ Bound} \approx \frac{3}{n}$$

For $n = 200$:

$$\frac{3}{200} = 0.0150 \quad (1.50\%)$$

---

## 3. Reporting Standard & Prohibited Claims

AegisTrace strictly forbids unqualified zero-FPR marketing statements.

### Prohibited Claim:
> *"AegisTrace has a 0% False Positive Rate."* (Scientifically invalid without population bounds).

### Approved Forensic Claim:
> *"Across $N = 200$ strictly sequestered negative and adversarial validation artifacts, AegisTrace produced $0$ false positives ($0 / 200$). The upper $95\%$ Clopper-Pearson exact confidence bound for the population False Positive Rate is $1.83\%$."*
