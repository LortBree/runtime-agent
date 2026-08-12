from layer1_environment import (
    State,
    SurvivalEnvironment,
)


environment = SurvivalEnvironment(
    initial_state=State(
        hunger=50.0,
        thirst=50.0,
        energy=80.0,
        curiosity=50.0,
    )
)

print("Initial:")
print(environment.observe())

print()
print("Running actions:")

for action in (
    "idle",
    "eat",
    "drink",
    "sleep",
    "work",
):

    transition = environment.step(action)

    print()
    print(f"Action: {action}")
    print(f"Before : {transition.state_before}")
    print(f"After  : {transition.state_after}")
    print(
        f"Day    : {transition.day}"
        f" | Phase: {transition.phase}"
    )