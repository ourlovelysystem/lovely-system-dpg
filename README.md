# Dear Peanut Gallery (DPG)

Dear Peanut Gallery (DPG) is a Q&A app where users post prompts and the
community answers — either in their own voice or through a "personality":
a reusable, model-backed persona defined by a set of prompts.

## Core concepts

- **Prompts** — posted by any user, open for anyone to answer.
- **Answers** — submitted as yourself, or by invoking a personality.
- **Personalities**
  - Built by users: a personality bundles a model choice plus a set of
    prompts that define how it answers.
  - Some personalities are **persistent** — kept around indefinitely by
    operator decision, not by popularity.
  - All other personalities are user-defined and subject to the lifecycle
    below.
- **Personality page** — exposes the model and the read-only prompts that
  define an existing personality. The same flow lets a user construct a
  new personality by writing their own prompts and choosing a model.
- **Voting** — single-click voting on personalities:
  - ⭐ **stars** to upvote, downvote via **boogers** (icon must actually
    look like a booger, not a generic emoji placeholder).
  - One vote per personality per session, maximum.
- **Favorites** — users can mark personalities as favorites.
- **Lifecycle / cleanup** — unpopular personalities are cleaned up sooner
  than popular ones. Before a personality expires, it posts a farewell
  message ("moving on to bigger and better career opportunities"),
  written in its own personality's voice.

## Authentication

Uses the same authentication scheme as
[Touchstone](https://touchstone.ourlovelysystem.org).

## UI

Top banner consistent with Touchstone's.

- The booger downvote icon must actually look like a booger.

## Open questions (not yet specified)

- How votes (stars/boogers) and favorites combine into a "popularity" score for cleanup purposes.
- Exact cleanup cadence/thresholds for unpopular vs. popular personalities.
- How persistent (operator-designated) personalities are flagged vs. user-created ones.
- Which models are available to users when constructing a personality.
- Whether farewell messages are generated live at expiry, or pre-drafted.
- Relationship between "favorites" and "stars" — same signal or two distinct ones (session-scoped vote vs. persistent favorite)?

## Status

Not yet built. This repo currently holds project documentation only.
