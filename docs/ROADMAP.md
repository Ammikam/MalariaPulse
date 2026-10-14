# MalariaPulse Development Roadmap

## Overview

This roadmap divides MalariaPulse into manageable phases, starting with a small end-to-end proof of concept and progressing toward a more capable, evaluated multi-agent system.

The phases are intended to guide team planning. Their completion depends on available data, existing models, and team capacity.

## Phase 1 — Project Foundation

**Goal:** Establish a shared understanding of the problem and create a reproducible development environment.

Tasks:

- [ ] Agree on the primary use case and intended users.
- [ ] Identify the first geographic area and reporting frequency.
- [ ] Review available malaria surveillance datasets.
- [ ] Identify the team's existing forecasting models.
- [ ] Document data sources, access restrictions, and limitations.
- [ ] Define common input and output schemas for all agents.
- [ ] Establish the Python environment and repository conventions.
- [ ] Prepare clearly labelled synthetic data for development.

**Deliverable:** A documented project foundation with agreed MVP boundaries.

## Phase 2 — Surveillance and Prediction Agent

**Goal:** Produce a preliminary risk assessment from surveillance data.

Tasks:

- [ ] Implement input validation and data-quality checks.
- [ ] Analyze weekly case counts and historical trends.
- [ ] Integrate the existing forecasting model, if suitable.
- [ ] Establish a baseline method for comparison.
- [ ] Define candidate risk indicators and document their assumptions.
- [ ] Evaluate predictions using historical data where available.
- [ ] Return structured results with evidence and limitations.
- [ ] Add tests for missing data, invalid values, and insufficient history.

**Deliverable:** A tested surveillance-analysis component that produces explainable outputs.

**Dependency:** Access to a suitable dataset and agreement on the modelling approach.

## Phase 3 — Supply and Resource Orchestration Agent

**Goal:** Convert surveillance findings and stock information into draft resource recommendations.

Tasks:

- [ ] Define an inventory data schema.
- [ ] Identify available facility and commodity information.
- [ ] Implement stock-level validation.
- [ ] Identify commodities below configured minimum levels.
- [ ] Use surveillance findings to prioritize locations for review.
- [ ] Generate recommendations with supporting inventory evidence.
- [ ] Add a human-approval status to all proposed actions.
- [ ] Test scenarios involving low stock, missing inventory, and incomplete risk assessments.

**Deliverable:** A supply-analysis component that generates reviewable inventory recommendations.

**Dependency:** A documented inventory dataset or a synthetic dataset for the initial demonstration.

## Phase 4 — Community Action and Intervention Agent

**Goal:** Generate clear, localized communication drafts from reviewed findings.

Tasks:

- [ ] Identify approved malaria prevention and early-diagnosis guidance.
- [ ] Define target audiences and communication formats.
- [ ] Create initial English message templates.
- [ ] Add Swahili message drafts.
- [ ] Ensure messages distinguish preliminary risk from a confirmed outbreak.
- [ ] Include a review status and supporting context.
- [ ] Arrange review of medical accuracy, translation, and local suitability.

**Deliverable:** A message-generation component that prepares drafts for authorized review.

**Dependency:** Access to approved guidance and appropriate language review.

## Phase 5 — Multi-Agent Orchestration

**Goal:** Connect the three agents into a single working workflow.

Tasks:

- [ ] Implement a central orchestrator.
- [ ] Pass structured outputs between agents.
- [ ] Define how failures and incomplete results are handled.
- [ ] Produce a consolidated report.
- [ ] Record input periods, assumptions, and relevant model versions.
- [ ] Add tests for normal execution and failure scenarios.
- [ ] Demonstrate the workflow using synthetic or approved sample data.

**Deliverable:** An end-to-end MalariaPulse prototype.

## Phase 6 — Agentic Tool Use

**Goal:** Introduce meaningful tool selection and coordinated reasoning.

Tasks:

- [ ] Identify the specific decisions that benefit from an LLM.
- [ ] Expose approved tools for data validation, forecasting, inventory checks, and reporting.
- [ ] Add tool calling to select and sequence appropriate analyses.
- [ ] Validate tool arguments and returned results.
- [ ] Separate deterministic calculations from generated explanations.
- [ ] Test invalid tool requests and unsupported claims.
- [ ] Log tool calls and relevant outputs for traceability.

**Deliverable:** A tool-using agent workflow that does more than generate text from a prompt.

**Note:** A multi-agent framework is optional. The team should choose one only if it improves clarity, reliability, or maintainability.

## Phase 7 — Interface and Human Review

**Goal:** Make the prototype accessible to researchers and reviewers.

Tasks:

- [ ] Build a basic interface or reporting view.
- [ ] Show surveillance results and data-quality warnings.
- [ ] Display evidence behind each preliminary risk assessment.
- [ ] Show stock recommendations and their underlying values.
- [ ] Present communication drafts for review.
- [ ] Add approval status and basic audit history.
- [ ] Ensure users can distinguish drafts from approved outputs.

**Deliverable:** A usable prototype interface for internal demonstration and evaluation.

## Phase 8 — Validation and Controlled Pilot Planning

**Goal:** Establish whether the system is reliable enough for further research or a carefully governed pilot.

Tasks:

- [ ] Conduct retrospective forecasting evaluation.
- [ ] Compare against suitable baselines.
- [ ] Assess false positives, missed signals, and reporting delays.
- [ ] Review the usefulness and feasibility of supply recommendations.
- [ ] Evaluate message accuracy and translation quality.
- [ ] Consult relevant epidemiology and public-health stakeholders.
- [ ] Review privacy, security, data access, and governance requirements.
- [ ] Define explicit criteria for any future pilot.

**Deliverable:** An evaluation report and a documented recommendation on whether further testing is justified.

## Suggested First Milestone

For the initial proof of concept, prioritize the smallest complete workflow:

1. Load a sample weekly surveillance dataset.
2. Run a transparent analysis or existing forecasting model.
3. Generate a preliminary risk assessment.
4. Check sample clinic inventory and draft recommendations.
5. Generate English and Swahili community message drafts.
6. Combine all outputs into one report.
7. Mark all consequential outputs as requiring human review.

Use synthetic data if approved real data is not yet available. Clearly label the demonstration and avoid claims of validated outbreak prediction.

## Definition of Done for the MVP

The MVP is ready for an internal demonstration when:

- [ ] A team member can run it using documented instructions.
- [ ] The data inputs and limitations are documented.
- [ ] All three agents contribute to the output.
- [ ] The workflow produces a consolidated report.
- [ ] Outputs are traceable to their inputs and assumptions.
- [ ] Basic tests pass.
- [ ] Human-review requirements are explicit.
- [ ] No unapproved real-world action or public message is triggered.

## Team Collaboration

Suggested areas of contribution:

- **Modelling:** forecasting integration, baselines, evaluation, and risk indicators.
- **Data engineering:** data sourcing, validation, schemas, and preprocessing.
- **Agent development:** orchestration, tool interfaces, and structured outputs.
- **Public-health research:** interpretation, guidance, and message review.
- **Testing and documentation:** reproducibility, test coverage, and project records.

The team can assign owners to individual tasks through GitHub Issues and track implementation using a GitHub Project board.

## Guiding Principle

Build a reliable, explainable end-to-end workflow first. Add autonomy, external integrations, and operational capabilities only when the evidence, validation, and governance are in place.
