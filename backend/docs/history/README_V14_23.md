# Forge Fitness v14.23 — Notifications + Proactive Coaching

Adds an in-app proactive coaching layer.

## Features
- Morning Forge brief based on today's workout and nutrition targets.
- Workout reminders before the scheduled workout time.
- Calendar conflict alerts with available alternate times when Google Calendar is connected.
- Evening protein reminders when protein intake is substantially behind target.
- Late-evening calorie/log reminders when intake is far below the current target.
- Notification center opened from the Home bell.
- Dismissible alerts.
- User settings for workout reminders, nutrition reminders, calendar conflicts, morning brief, and reminder lead time.
- Home screen proactive alert card.
- AI Coach `daily brief` intent and `/me/coach/daily-brief` endpoint.

These are in-app reminders generated from the user's real local clock, workout schedule,
calendar integration, and Nutrition log. They do not require a separate notification API key.
