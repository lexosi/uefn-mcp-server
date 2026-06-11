# Media

`loop.gif` — a short screen recording of the visual feedback loop, embedded at
the top of the main README. It must be recorded by hand: the editor viewport
cannot be captured headless.

What to capture (3–5 seconds):

1. The agent calls `get_viewport_screenshot`; the returned image appears in chat.
2. The agent makes one visible edit (move or spawn an actor).
3. The agent screenshots again; the change is visible in the second image.

The takeaway for a viewer: the model sees its own change and closes the loop.
