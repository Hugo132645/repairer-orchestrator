# Portal themes

The portal ships with two visual modes:

- **Technology** (default): dark black/navy surfaces, blue-purple gradients,
  glass panels, luminous status accents, and low-motion background waves.
- **Classic**: the original cream-and-green Repairer Desk interface.

Use the floating theme button at the lower-right corner on either the login page
or inside the portal. The choice is stored only in browser `localStorage`; it
does not affect an account, conversation, or another user's browser.

Theme files:

```text
repairer_portal/static/styles.css                 Maintained classic/base theme
repairer_portal/static/themes/tech.css            Technology overrides
repairer_portal/static/themes/classic/styles.css  Pre-redesign snapshot
```

To make Classic the default, change the `<body>` class in `index.html` and the
`savedTheme` fallback in `app.js` from `tech` to `classic`. The technology theme
respects the operating system's reduced-motion preference.
