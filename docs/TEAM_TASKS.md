# Team tasks

Lead: _name_ · Submission owner (fills in the form): _name_

## Before anyone starts
- [ ] Confirm the official build-window start and end dates (ask the organisers). **Do not push commits after the end date.**
- [ ] Confirm MKU allows any data or model to be made public. Use synthetic or public data and a new simple model unless cleared.
- [ ] Everyone clones the repo, runs `pytest`, and runs the pipeline once.

## Modelling (modellers)
- [ ] Review `src/malariapulse/forecast.py`: are the signals sensible? Adjust thresholds.
- [ ] Optionally replace `assess_zone` with a better model (keep the function signature).
- [ ] Review the synthetic data assumptions in `scripts/generate_synthetic_data.py`.
- [ ] Explore real environmental data (Open-Meteo / NASA POWER) in `mcp_servers/environment_server.py`.

## Agents and MCP (developer 1)
- [ ] Test `--mode llm` with a Gemini key; fix any SDK or schema issues in `llm.py`.
- [ ] Tune the three agent prompts in `agents.py`.
- [ ] Add one more useful MCP tool if time allows (e.g. a data-quality checker).

## Dashboard and deployment (developer 2)
- [ ] Polish `app/review_app.py` (layout, a risk summary table for all zones, a map if time allows).
- [ ] Deploy (Streamlit Community Cloud / Hugging Face Spaces); set `GEMINI_API_KEY` as a secret, not in the repo.
- [ ] Test the demo link from a different device.

## Documentation and demo (everyone, owner: _name_)
- [ ] Keep the README build log honest and current.
- [ ] Record a 2-3 minute demo video: run agents, show flagged zones, show the tool-call audit trail, approve one proposal and reject another.
- [ ] Final check of the challenge checklist in the README.
- [ ] Submit the form (repo URL, demo URL, video URL, architecture diagram, descriptions).

## Daily check-in
Post a short update in the group: done / blocked / next.
