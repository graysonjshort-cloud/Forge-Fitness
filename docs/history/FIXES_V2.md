# Repair v2

Fixed the rest timer bug:
- timer state is now initialized
- entering the timer screen starts `setInterval`
- leaving the timer screen stops it
- the countdown uses the exercise's real `rest_seconds`
- Skip Rest clears the timer and returns to the exercise

Also corrected:
- weight is sent to the API when a set is logged
- active workout session restores after refresh
- saved profile values hydrate the preferences form
