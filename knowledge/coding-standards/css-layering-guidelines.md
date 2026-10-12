
# CSS Layering Guidelines

## Header

The header should use the project's documented layering token.

Avoid arbitrary z-index values unless there is a documented reason for the chosen value.

## Modal Dialogs

Modal dialogs must appear above the header and page content.

Use the shared modal layer token rather than hardcoded z-index values.

## Overlays

Overlays should follow the documented layering order for the application.

When changing stacking behavior, verify the interaction with headers, dialogs, dropdowns, and other overlays.
