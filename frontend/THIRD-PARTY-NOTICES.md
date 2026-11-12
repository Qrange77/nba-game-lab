# TailAdmin Vue Free

Source: https://github.com/TailAdmin/vue-tailwind-admin-dashboard

Revision: `6d5a3657c3d1562b2b8488c6f54886920b798326`

`src/assets/tailadmin.css` contains the upstream Tailwind v4 theme, base rules,
and sidebar menu utilities. `src/components/ui/Button.vue` is the upstream button
component. The responsive sidebar shell is adapted for conversation history in
`src/components/ConversationSidebar.vue`. The Agent-specific views and chat
integration are custom to NBA Game Lab. This uses only the free edition.

TailAdmin's MIT copyright and license are preserved in `TAILADMIN-LICENSE`.

# Research execution graph

Design reference: https://www.assistant-ui.com/elements/flow-graph

The research graph is a native Vue implementation of the documented dependency
column, curved edge and progressive reveal interaction. It does not install the
React component or assistant-ui runtime. Node lifecycle, per-node tool inspection,
concurrency measurements and round tracking are specific to this application.
