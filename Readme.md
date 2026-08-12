# Runtime Agent

## Project Overview

Runtime Agent is an experimental project exploring the design of a **persistent self-learning autonomous agent**.

The project investigates how an agent can learn from its own interaction experience, transform those experiences into reusable knowledge, and retain that knowledge across operational cycles and process restarts.

The core architecture is built around three layers:

```text
┌──────────────────────────────┐
│ Entity Core                  │
│ Observation • Decision       │
│ Action • Learning            │
└──────────────┬───────────────┘
               │
┌──────────────┴───────────────┐
│ Knowledge Layer              │
│ Learned Relations • Memory   │
│ Action Registry              │
└──────────────┬───────────────┘
               │
┌──────────────┴───────────────┐
│ Environment                  │
│ State • Time • Consequences  │
└──────────────────────────────┘
````

The agent operates through an iterative learning cycle:

```text
Observe
   ↓
Retrieve Knowledge
   ↓
Decision
   ↓
Select Action
   ↓
Execute
   ↓
Observe Result
   ↓
Generate Experience
   ↓
Learn Relation
   ↓
Update Knowledge
   ↓
Repeat
```

A key architectural principle is the separation between the **Entity Core** and the **persistent Knowledge Layer**. The Entity Core represents the running agent process, while learned knowledge exists independently and can survive process failure or restart.

The initial implementation uses a controlled survival environment to study the learning and decision mechanisms before extending the system toward more complex environments and dynamically acquired capabilities.

---

## Research Approach

Runtime Agent is developed as a sequence of controlled experiments.

Each version is treated as an experimental stage rather than assumed to be an improvement. Earlier versions are preserved in Git so that behavior can be reproduced and compared against frozen baselines.

The development loop is:

```text
Implement
   ↓
Unit Test
   ↓
Controlled Runtime Experiment
   ↓
Instrument Behavior
   ↓
Identify Failure Mode
   ↓
Refine Policy
```

The goal is not to optimize a single run, but to identify which mechanisms are actually supported by empirical evidence.

---

## Current Architecture

### Layer 1 — Environment

The Environment defines:

- state variables;
    
- available actions;
    
- time progression;
    
- action consequences;
    
- state boundaries and transitions.
    

The current controlled environment is designed primarily for studying survival and adaptation behavior.

### Layer 2 — Knowledge

The Knowledge Layer stores learned relations derived from actual experience.

Relations are conditioned by:

```text
State Context
+
Action
+
State Variable
```

and contain information such as:

```text
Learned Magnitude
Confidence
Support
Contradiction
Evidence
```

Knowledge is updated from the observed transition:

```text
State Before
    ↓
Action
    ↓
State After
    ↓
Observed Delta
    ↓
Learned Relation
```

The learning mechanism is based on accumulated and decayed evidence rather than hard-coded nominal action effects.

### Layer 3 — Entity / Decision

The Entity Core orchestrates the runtime cycle:

```text
Observe
   ↓
Retrieve Knowledge
   ↓
Decision
   ↓
Execute
   ↓
Generate Experience
   ↓
Learn
```

Decision is separated from knowledge storage so that policy behavior can be experimentally changed without rewriting the learning layer.

---

## Experimental Progress

### V0.5.1 — Persistent Learned Relations

V0.5.1 established the baseline implementation for:

- experience-based learning;
    
- state-conditioned learned relations;
    
- persistent knowledge;
    
- restartable agent processes;
    
- controlled survival simulation;
    
- evidence accumulation and decay;
    
- confidence-based relations;
    
- decision scoring from learned relations.
    

The 500-cycle baseline survived successfully.

However, the experiment exposed a decision pathology:

```text
No positive current-context score
        ↓
Select highest known score
        ↓
Zero-score action repeatedly selected
        ↓
Sleep lock
```

The baseline therefore became the reference point for subsequent policy experiments.

---

### V0.5.2 — Novelty-Based Exploration

V0.5.2 introduced a separate exploration mechanism for the no-positive-score regime.

The policy became:

```text
Positive current-context score
        ↓
     Exploit

No positive score
        ↓
   Explore by novelty
```

Novelty is derived from evidence maturity:
$$  
N(E)=\frac{k}{E+k}  
$$

where:

- `E` is accumulated evidence;
    
- `k` is the smoothing constant.
    

This successfully removed the V0.5.1 sleep lock and produced much greater action diversity.

However, the 500-cycle experiment exposed a second pathology:

```text
No positive score
        ↓
Explore
        ↓
Knowledge becomes mature
        ↓
Explore continues
        ↓
Exploration lock
```

The result demonstrated that novelty-based exploration needs a stopping condition.

---

### V0.5.3 — Exploration Saturation and Neutral Regime

V0.5.3 introduced a third decision regime based on novelty saturation.

The policy became:

```text
Positive score
      ↓
   Exploit

No positive score
      ↓
Novelty above threshold?
   ┌──────┴──────┐
  yes            no
   ↓              ↓
Explore        Neutral
```

The initial saturation threshold is:

$$  
\tau=0.25  
$$

with:

$$
N(E)=\frac{5}{E+5}  
$$

which places the saturation boundary at approximately:

$$  
E\ge15  
$$

Once exploration is saturated, V0.5.3 uses a least-harm objective:

$$  
a^*=\arg\min_a Harm(a|S)  
$$

This successfully reduced exploration from the V0.5.2 regime and established an explicit neutral state.

However, the 500-cycle experiment exposed another policy pathology:

```text
No positive score
        ↓
Knowledge saturated
        ↓
Least-harm selection
        ↓
Zero-harm action repeatedly selected
        ↓
Drink lock
```

The issue is not that the harm calculation fails. The problem is that:

$$  
\text{minimum harm}  
\neq  
\text{most appropriate neutral behavior}  
$$

An action can have zero predicted harm while still being unnecessary.

Therefore, **neutral behavior remains an active research problem**.

---

## Current Research Focus

The current focus is the design of a robust decision policy for the **non-positive utility regime**.

The system currently distinguishes three behavioral regimes:

```text
Exploit
→ a positive learned utility exists

Explore
→ no positive utility exists,
  but knowledge is still immature

Neutral
→ no positive utility exists,
  and knowledge is saturated
```

The remaining research question is:

> When no action provides positive utility and knowledge is already saturated, how should the agent choose an action without producing another repetitive action lock?

The next policy iterations will therefore focus on defining a stronger **neutral objective**, rather than modifying the Knowledge Layer.

---

## Versioning Principle

Each version is evaluated against a frozen predecessor.

The current progression is:

```text
V0.5.1
Baseline
   ↓
Sleep Lock identified

V0.5.2
Novelty Exploration
   ↓
Sleep Lock reduced
   ↓
Exploration Lock identified

V0.5.3
Saturation + Neutral Regime
   ↓
Exploration Lock reduced
   ↓
Neutral / Zero-Harm Lock identified
```

This progression is intentional.

A new version is not considered successful merely because one pathology disappears. It must also be evaluated for the new behavior introduced by the change.

---

## Empirical Development Principle

The architecture and capabilities of later versions are determined by the empirical results of earlier stages rather than being assumed in advance.

This means:

```text
Observation
   ↓
Measurement
   ↓
Hypothesis
   ↓
Minimal Policy Change
   ↓
Controlled Experiment
   ↓
New Evidence
```

The project therefore treats behavioral failures as research findings rather than errors to be hidden.

---

## Long-Term Direction

The project is intended to progressively explore:

```text
Persistent Knowledge
        ↓
Continual Adaptation
        ↓
Robust Decision Policies
        ↓
Dynamic Skill Acquisition
        ↓
Runtime Environment
```

The role of an LLM is explored as an **observation and experience interpretation component**, rather than as the underlying learning mechanism.

The long-term architecture remains deliberately open. Later capabilities will be introduced only when the preceding experimental stages provide sufficient evidence that the underlying mechanism is working as intended.