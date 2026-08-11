# Runtime Agent

## Project Overview

Runtime Agent is an experimental project exploring the design of a **persistent self-learning autonomous agent**.

The project investigates how an agent can learn from its own interaction experience, transform those experiences into reusable knowledge, and retain that knowledge across operational cycles and process restarts.

The core concept is built around three layers:

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

A key design principle is the separation between the **Entity Core** and the **persistent Knowledge Layer**. The Entity Core represents the running agent process, while learned knowledge exists independently and can survive process failure or restart.

The initial implementation uses a controlled survival environment to study this mechanism before extending the system toward more complex environments and dynamically acquired capabilities.

### Current Focus

**V0.5.1 — Persistent Learned Relations**

The current version focuses on:

- experience-based learning;
    
- state-conditioned learned relations;
    
- persistent knowledge;
    
- restartable agent processes;
    
- controlled survival simulation.

The role of an LLM is explored as an **observation and experience interpretation component**, rather than as the underlying learning mechanism.

### Long-Term Direction

The project is intended to progressively explore:

```text
Persistent Knowledge
        ↓
Continual Adaptation
        ↓
Dynamic Skill Acquisition
        ↓
Runtime Environment
```

The architecture and capabilities of later versions will be determined by the empirical results of the earlier stages rather than being assumed in advance.