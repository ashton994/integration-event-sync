# integration-event-sync

A small Python project I built to practice API integrations and incremental data sync.

## What it does
This script fetches repository events from the GitHub API, stores them in `output.json`, and keeps track of the latest processed event ID in `state.json` so only new events are collected on the next run.

## Main concepts
- REST API calls with Python `requests`
- environment-based configuration
- retry handling for rate limits
- incremental sync with checkpoints
- JSON output and local state management

## Why I built it
I wanted to strengthen my hands-on understanding of API integrations, retries, and system behavior beyond Postman-level testing.

## What I learned
- how to structure API calls in code
- how to handle rate limiting and retries
- how to track state between runs
- how integration logic becomes more reliable with checkpointing
