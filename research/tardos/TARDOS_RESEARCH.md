# Collusion-Resistant Fingerprinting & Tardos Traitor-Tracing Research

**Project:** SIH26237 — Cryptographic Attribution & Immutable Decryption Provenance  
**Author:** Agent 2 (Principal Applied Cryptography + Fingerprinting Research Engineer)  
**Date:** September 2026  
**Document Status:** Complete Scientific Specification  

---

## 1. Introduction & Problem Statement
In multi-recipient distribution of confidential digital assets, malicious recipients may form a **coalition** $C \subseteq \{1, \dots, N\}$ of size $|C| \le c$. By comparing their individual copies, the colluders identify positions where their assigned codewords differ and synthesize a forged/hybrid document (e.g., via interleaving, majority voting, random symbol selection, or erasure attacks) in an attempt to hide their identities or frame an innocent user.

Classical traitor-tracing schemes (such as Boneh-Shaw 1998) required code lengths exponential or polynomial with high degree ($O(c^4 \log N)$ or $O(c^3 \log N)$). Gábor Tardos (STOC 2003, J. ACM 2008) introduced an asymptotically optimal probabilistic fingerprinting code of length:
$$m = O(c^2 \ln(N / \epsilon_1))$$
where:
- $N$ is the total population of authorized recipients,
- $c$ is the maximum coalition size the code is designed to resist,
- $\epsilon_1$ is the maximum allowable probability of falsely accusing an innocent recipient.

---

## 2. Mathematical Foundations

### A. The Original Tardos Construction (2003 / 2008)
Let $N$ be the number of recipients and $m$ the code length (number of carrier mark positions).
1. **Bias Distribution**: A secret bias vector $\mathbf{p} = (p_1, \dots, p_m) \in [t, 1-t]^m$ is chosen independently for each column $j \in \{1, \dots, m\}$ according to the continuous probability density function:
   $$f(p) = \frac{1}{2 \arcsin(1 - 2t)} \cdot \frac{1}{\sqrt{p(1-p)}} \quad \text{for } p \in [t, 1-t]$$
   where $t$ is a cutoff parameter chosen as $t = \frac{1}{300c}$.
   Using the change of variables $p = \sin^2 \theta$, the cumulative distribution is $F(p) = \frac{2}{\pi} \arcsin\sqrt{p}$ (when $t \to 0$), allowing sampling via:
   $$p_j = \sin^2\left(t' + r_j \left(\frac{\pi}{2} - 2t'\right)\right), \quad r_j \sim \mathcal{U}[0, 1], \quad t' = \arcsin\sqrt{t}$$
2. **Codebook Generation**: For recipient $i \in \{1, \dots, N\}$ and symbol $j \in \{1, \dots, m\}$, the codeword symbol $X_{i,j} \in \{0, 1\}$ is generated independently with:
   $$\mathbb{P}(X_{i,j} = 1) = p_j, \quad \mathbb{P}(X_{i,j} = 0) = 1 - p_j$$
3. **The Marking Assumption**:
   For any position $j \in \{1, \dots, m\}$, if all colluders $k \in C$ possess the identical symbol $X_{k,j} = b \in \{0, 1\}$, they are forced to emit $y_j = b$. If the colluders possess differing symbols (i.e., at least one colluder has 0 and at least one has 1), they may emit $y_j \in \{0, 1\}$ or an erasure symbol $\bot$ according to an arbitrary, possibly randomized strategy.
4. **Original Scoring Function**:
   Tardos originally defined an asymmetric score function:
   $$U(y_j, X_{i,j}, p_j) = \begin{cases}
   +\sqrt{\frac{1-p_j}{p_j}} & \text{if } y_j = 1 \text{ and } X_{i,j} = 1 \\
   -\sqrt{\frac{p_j}{1-p_j}} & \text{if } y_j = 1 \text{ and } X_{i,j} = 0 \\
   0 & \text{if } y_j = 0
   \end{cases}$$
   Accumulated user score: $S_i = \sum_{j=1}^m U(y_j, X_{i,j}, p_j)$.
5. **Threshold & Accusation**:
   Tardos set code length $m = 100 c^2 \ln(N / \epsilon_1)$ and threshold $Z = 20 c \ln(N / \epsilon_1)$. A recipient $i$ is accused if $S_i > Z$.

---

### B. The Symmetric Tardos Code (Škorić et al. 2008)
The original Tardos code discarded information whenever $y_j = 0$. Škorić, Katzenbeisser, and Celik (2008) formulated the **Symbol-Symmetric Tardos Code**, scoring both symbols symmetrically:
$$U_{sym}(y_j, X_{i,j}, p_j) = \begin{cases}
+\sqrt{\frac{1-p_j}{p_j}} & \text{if } y_j = 1 \text{ and } X_{i,j} = 1 \\
-\sqrt{\frac{p_j}{1-p_j}} & \text{if } y_j = 1 \text{ and } X_{i,j} = 0 \\
-\sqrt{\frac{1-p_j}{p_j}} & \text{if } y_j = 0 \text{ and } X_{i,j} = 1 \\
+\sqrt{\frac{p_j}{1-p_j}} & \text{if } y_j = 0 \text{ and } X_{i,j} = 0
\end{cases}$$

#### Key Theorem: Zero Expectation for Innocent Users
For any innocent recipient $i \notin C$, regardless of the colluders' strategy $y_j$:
$$\mathbb{E}[U_{sym}(1, X_{i,j}, p_j)] = p_j \sqrt{\frac{1-p_j}{p_j}} - (1-p_j) \sqrt{\frac{p_j}{1-p_j}} = \sqrt{p_j(1-p_j)} - \sqrt{p_j(1-p_j)} = 0$$
$$\mathbb{E}[U_{sym}(0, X_{i,j}, p_j)] = -p_j \sqrt{\frac{1-p_j}{p_j}} + (1-p_j) \sqrt{\frac{p_j}{1-p_j}} = 0$$
$$\implies \mathbb{E}[S_i] = 0 \quad \forall i \notin C$$
In contrast, for any guilty colluder $k \in C$, their symbols correlate with $y_j$, so their expected score is strictly positive and proportional to $m/c$:
$$\sum_{k \in C} \mathbb{E}[S_k] \ge \frac{2}{\pi} m$$

---

### C. Parameter Optimization & Capacity Bounds (Blayer & Tassa 2008)
Blayer and Tassa showed that Tardos' original constant $d_{\ell} = 100$ was overly conservative. By decoupling the false accusation bound $\epsilon_1$ from the false negative bound $\epsilon_2$, they proved:
$$m \ge \lceil \kappa \cdot c^2 \ln(N / \epsilon_1) \rceil$$
Where:
- Original Tardos: $\kappa = 100$
- Blayer-Tassa Optimized: $\kappa \approx 20$ to $25$
- Asymptotic Lower Bound (Information Theoretic Capacity): $\kappa_{min} = \frac{\pi^2}{2} \approx 4.93$
- Threshold Formula:
  $$Z = \alpha \cdot \frac{m}{c} \quad \text{with } \alpha \in [0.2, 0.4]$$
  Or analytically using the Chernoff/Bernstein bound:
  $$Z = \sqrt{2 m \ln(N / \epsilon_1)}$$

---

## 3. Investigation of Existing Reusable Code & Implementations

| Repository / Source | Author / Org | License | Focus / Language | Reusability Evaluation |
| :--- | :--- | :--- | :--- | :--- |
| `erodriguezlois/BlackCATT` | E. Rodriguez-Lois et al. | MIT / Apache | Federated Learning watermarking; Python/PyTorch | **REJECT AS DIRECT DEPENDENCY**: Research scripts using static precomputed CSV tables for specific client sizes rather than dynamic cryptographic codebook generation. Useful for reference. |
| `pmeerw/watermarking` & publications | Peter Meerwald / Teddy Furon | Academic / Research (INRIA) | Joint decoding ("Don Quixote"); C / MATLAB | **ADAPT MATHEMATICALLY**: Algorithms published in IEEE TIFS 2012. No standalone installable Python package exists. Equations adapted directly into clean Python. |
| `GTAC-ITEAM-UPV/separating-codes` | UPV Research | GPLv3 | Combinatorial separating codes / C++ | **REJECT**: Incompatible license (GPLv3) and different mathematical target (separating arrays vs. probabilistic Tardos). |
| `ashebbar-dev/SIH` | Competitor Archive | None / Proprietary | SIH Hackathon prototype | **REJECT**: No verified open source license; fragile heuristic markers rather than genuine probabilistic Tardos codes. |
| Standard PyPI (`pip`) | Community | N/A | No standard `tardos` package found | **IMPLEMENT**: Pure Python implementation required. |

### Reuse Decision Matrix
- **Mathematical Framework**: **REUSE / ADAPT** published formulas from Gábor Tardos (2003, 2008), Boris Škorić et al. (2008), and Blayer & Tassa (2008).
- **Core Engine**: **IMPLEMENT** a self-contained, clean, zero-dependency (using Python standard library + hashlib/hmac/math) module implementing `SymmetricTardosEngine`.
- **Capacity Planner**: **IMPLEMENT** mathematically grounded parameter validation enforcing fail-closed bounds.
- **Provider Glue**: **IMPLEMENT** `TardosTraceabilityProvider` cleanly inheriting from the existing `TraceabilityProvider` interface without breaking legacy callers.

---

## 4. Attack Models & Marking Assumption Violations

1. **Simple Majority Attack**: Colluders vote on each bit position $j$. If ones exceed zeros, $y_j = 1$, else $0$.
2. **Interleaving Attack**: For each bit position $j$, colluders uniformly pick one colluder $k \in C$ at random and set $y_j = X_{k,j}$.
3. **Worst-Case Collusion (Minimax Strategy)**: Colluders evaluate the public bias distribution $f(p)$ and select $y_j$ to minimize the maximum expected score of their members.
4. **Coin-Flip / Random Symbol**: If symbols differ, colluders output $\text{Bernoulli}(0.5)$.
5. **Erasure / Noise Channel**: Colluders introduce random bit flips with probability $P_e$ or corrupt symbols ($\bot$).
6. **Codebook Mismatch**: Attempting to decode an extracted fingerprint using a codebook bound to a different document/release. Must yield zero correlation / `ABSTAIN`.

---

## 5. Formal Security Boundary & Non-Claims

> [!IMPORTANT]
> **What Tardos Guarantees:**
> - Under the Marking Assumption, for any coalition of size $\le c$, with code length $m \ge \kappa c^2 \ln(N / \epsilon_1)$ and threshold $Z$, the probability that *any* innocent recipient is accused is strictly $\le \epsilon_1$.
> - At least one colluder receives an expected score exceeding the threshold with probability $1 - \epsilon_2$.

> [!WARNING]
> **What Tardos DOES NOT Guarantee:**
> - It is **not** an image/PDF watermark by itself; it requires an underlying carrier embedding channel.
> - If an adversary alters symbols outside the Marking Assumption (e.g. carrier destruction or massive bit erasures $> 50\%$), detection probability degrades to `INSUFFICIENT_EVIDENCE` / `NO_SIGNAL`.
> - It does not prevent unwatermarked analog re-typing of document semantics.
