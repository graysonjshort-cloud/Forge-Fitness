# Forge Fitness v14.18.1 — Food Intent Fix

Fixed the AI Coach so direct commands such as `log a zero sugar root beer`,
`add a sandwich`, `track my protein shake`, and `I drank a Coke Zero` enter
Smart Food Logging instead of falling through to the generic workout response.

Training commands such as `log my workout`, `track my reps`, and
`record my bench press` are explicitly excluded from the nutrition router.

The restaurant/brand lookup, clarification, confirmation, and logging behavior
from v14.18 is unchanged.
