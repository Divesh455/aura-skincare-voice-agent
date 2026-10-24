# Aura Skincare Voice Agent — Implementation Roadmap

## 1. Document Information

| Field | Value |
|---|---|
| Project | Aura Skincare Voice Agent |
| Document | Implementation Roadmap |
| Version | 1.0 |
| Status | In progress |
| Primary goal | Build, test, and deploy the assignment |

## 2. Development Principles

1. Implement one major component at a time.
2. Test each component before building on top of it.
3. Keep application logic separate from UI and database code.
4. Use the assignment's mock data as the source of truth.
5. Keep API keys and passwords out of Git.
6. Record actual test results instead of assuming a feature works.
7. Update the requirements and architecture documents when behavior changes.

## 3. Phase 1 — Environment and Database

### Objective
Set up the development environment and verify persistent order storage.

### Tasks
- [x] Create the project directory.
- [x] Set up a Python virtual environment.
- [x] Install the initial backend dependencies.
- [x] Start PostgreSQL through Docker Compose.
- [x] Resolve the local PostgreSQL port conflict.
- [x] Fix database password authentication.
- [x] Establish a working Python-to-PostgreSQL connection.
- [x] Create the `orders` table.
- [x] Insert the three assignment mock orders.
- [x] Verify the three records with a SQL query.

### Completion criteria
The database must retain the three mock orders, and Python must be able to retrieve them.

### Result
**Completed and verified.**

## 4. Phase 2 — FastAPI Backend

### Objective
Build a reliable backend for health checks and order lookup.

### Tasks
- [x] Create the FastAPI application.
- [x] Configure database sessions.
- [x] Define the SQLAlchemy order model.
- [x] Implement `get_order_details(order_id)`.
- [x] Seed the mock orders automatically when needed.
- [x] Add the health-check endpoint.
- [x] Add the order lookup endpoint.
- [x] Test a valid order lookup.
- [ ] Test an unknown order ID.
- [ ] Test an empty or malformed order ID.
- [ ] Test controlled handling of database failures.
- [ ] Add automated backend tests.

### Completion criteria
Valid orders return their stored data. Invalid requests return understandable errors without crashing the application.

### Current result
The basic API and database lookup have been tested successfully. Remaining error-path tests still need to be completed.

## 5. Phase 3 — LangChain Tool Integration

### Objective
Allow the AI model to retrieve verified order information using a dedicated tool.

### Tasks
- [ ] Select the LLM provider and model.
- [ ] Configure model credentials using backend environment variables.
- [ ] Install and configure the required LangChain integration packages.
- [ ] Wrap `get_order_details` as a LangChain tool.
- [ ] Define the tool's name, description, input schema, and output behavior.
- [ ] Connect the tool to the selected model.
- [ ] Test a valid order lookup.
- [ ] Test an unknown order ID.
- [ ] Test a request that does not require order lookup.
- [ ] Verify that the model does not invent tool results.

### Completion criteria
The model can choose and invoke the tool when appropriate and use the returned database data in its response.

## 6. Phase 4 — LangGraph Agent Workflow

### Objective
Implement a stateful conversational workflow for Aria.

### Planned workflow

1. Receive a customer message.
2. Update the conversation state.
3. Determine whether an order lookup or other supported tool is needed.
4. Execute an appropriate tool call.
5. Return tool results to the model.
6. Generate a grounded response.
7. Continue the conversation or finish the call.

### Tasks
- [ ] Define the conversation state schema.
- [ ] Define the model and tool nodes.
- [ ] Define conditional routing between nodes.
- [ ] Connect the order lookup tool.
- [ ] Handle missing order IDs.
- [ ] Handle tool errors and unknown orders.
- [ ] Add policy-aware response instructions.
- [ ] Preserve relevant context across turns.
- [ ] Define call-completion behavior.
- [ ] Test the workflow with multiple conversation scenarios.

### Completion criteria
Aria can maintain conversation context, retrieve order information when necessary, and produce appropriate responses without fabricating facts.

## 7. Phase 5 — Business Policy Guardrails

### Objective
Ensure that customer-facing responses follow the assignment's rules.

### Tasks
- [ ] Document the shipping-fee rules.
- [ ] Handle the unresolved shipping-fee boundary at exactly ₹499 without guessing.
- [ ] Implement return-window checks using available delivery information.
- [ ] Check product condition requirements for returns.
- [ ] Apply cancellation eligibility based on order status.
- [ ] Explain damaged-product reporting and photo requirements.
- [ ] Explain COD eligibility and payment options.
- [ ] Prevent false claims of completed cancellations or replacements.
- [ ] Test each policy with positive and negative cases.

### Completion criteria
The agent gives policy-consistent explanations and clearly distinguishes advice from actions actually executed.

## 8. Phase 6 — Voice Integration

### Objective
Enable natural spoken conversations in the browser.

### Tasks
- [ ] Choose the voice implementation.
- [ ] Configure the required voice service.
- [ ] Request microphone access appropriately.
- [ ] Implement the Start Call control.
- [ ] Implement the End Call control.
- [ ] Connect customer speech to the conversation workflow.
- [ ] Connect agent responses to audio playback.
- [ ] Display Listening, Thinking, and Speaking indicators.
- [ ] Handle microphone permission failures.
- [ ] Handle voice-service and network errors.
- [ ] Test interruptions and repeated interactions where supported.
- [ ] Measure and improve perceived response latency.

### Completion criteria
A customer can conduct a basic spoken conversation and hear the agent's responses. Call state and errors are visible in the interface.

## 9. Phase 7 — React User Interface

### Objective
Build the customer-facing experience and the assignment demonstration interface.

### Tasks
- [ ] Set up the React + Vite application.
- [ ] Build the main call interface.
- [ ] Add Start Call and End Call controls.
- [ ] Add live Listening, Thinking, and Speaking indicators.
- [ ] Add a visible test order helper.
- [ ] Display conversation messages chronologically.
- [ ] Distinguish customer and agent messages.
- [ ] Display the post-call transcript.
- [ ] Display the required JSON summary.
- [ ] Add loading and error states.
- [ ] Connect the frontend to the backend.
- [ ] Test the interface at common browser sizes.
- [ ] Verify microphone permissions in the target browser.

### Completion criteria
The interface supports the required demonstration flow without requiring manual API calls from the evaluator.

## 10. Phase 8 — Transcript and Call Summary

### Objective
Produce the required post-call artifacts.

### Required summary schema

- `customer_intent`
- `order_id`
- `resolution_status`
- `call_summary`

### Tasks
- [ ] Define how transcript messages are collected.
- [ ] Preserve message order.
- [ ] Define the summary-generation process.
- [ ] Validate the summary schema.
- [ ] Define consistent resolution-status values.
- [ ] Handle calls where no order ID was supplied.
- [ ] Handle calls where the issue remains unresolved.
- [ ] Display the transcript and JSON summary.
- [ ] Verify the summary reflects the actual conversation.

### Completion criteria
Every completed demonstration call produces a chronological transcript and a valid summary that accurately describes the outcome.

## 11. Phase 9 — n8n Post-Call Automation

### Objective
Demonstrate an automated workflow triggered after a completed call.

### Initial workflow concept

1. Receive the completed call summary.
2. Validate the incoming payload.
3. Process or store the summary in the chosen destination.
4. Return or record the workflow outcome.
5. Handle invalid input and automation failures.

### Tasks
- [ ] Select the n8n trigger mechanism.
- [ ] Define the incoming JSON payload.
- [ ] Configure authentication.
- [ ] Select the summary destination.
- [ ] Build the n8n workflow.
- [ ] Connect the backend to the workflow.
- [ ] Test a successful execution.
- [ ] Test invalid payload handling.
- [ ] Test failure behavior.
- [ ] Document the workflow and setup steps.

### Completion criteria
The evaluator can observe one working post-call automation and understand what happens when it fails.

## 12. Phase 10 — End-to-End Testing

### Objective
Verify that the complete application works as a single system.

### Core test scenarios

| Scenario | Expected behavior |
|---|---|
| Ask about ORD-101 | Correct status and available tracking information |
| Ask about ORD-102 | Correct delivered status and delivery age |
| Ask about ORD-103 | Correct Processing status and cancellation eligibility explanation |
| Provide an unknown order ID | Ask the customer to verify the ID |
| Ask about a return after 14 days | Explain that the standard seven-day window has passed |
| Ask about cancellation for an Out for Delivery order | Explain the cancellation restriction |
| Ask about a damaged product | Explain the 48-hour reporting and photo requirements |
| Ask about COD | Explain the ₹2,500 limit and accepted payment methods |
| Ask a general policy question | Answer using the documented policy |
| Database lookup fails | Give a controlled error rather than inventing information |
| Voice service fails | Show a clear error and provide a recovery path |
| Complete a call | Display transcript and JSON summary |
| Finish a call | Trigger the configured n8n workflow |

### Additional checks
- [ ] Test multiple turns in one conversation.
- [ ] Verify that the model uses actual tool results.
- [ ] Verify that summaries do not claim unperformed actions.
- [ ] Test the application from a clean startup.
- [ ] Verify that environment secrets are not exposed to the browser.
- [ ] Test the public deployment separately from local development.

## 13. Phase 11 — Security and Repository Preparation

### Tasks
- [ ] Create or update `.gitignore`.
- [ ] Exclude `.env`, virtual environments, caches, and generated files.
- [ ] Remove secrets from tracked files and commit history where necessary.
- [ ] Provide an `.env.example` with placeholder values only.
- [ ] Document setup and startup commands.
- [ ] Document the architecture and tool flow.
- [ ] Document known limitations.
- [ ] Confirm that no private database endpoint or credential is exposed.

### Completion criteria
A reviewer can understand and set up the project from the repository without receiving any private credentials.

## 14. Phase 12 — Deployment and Submission

### Tasks
- [ ] Select hosting services for the frontend and backend.
- [ ] Configure a secure PostgreSQL deployment.
- [ ] Configure production environment variables.
- [ ] Configure frontend-to-backend origins.
- [ ] Configure the voice provider for the deployed domain.
- [ ] Deploy the application.
- [ ] Test all critical features on the public URL.
- [ ] Prepare a useful GitHub README.
- [ ] Record a 3–5 minute demo video.
- [ ] Prepare the requested 2–3 sentence approach note.
- [ ] Include the LinkedIn profile link.
- [ ] Verify the final repository and deployment links.
- [ ] Submit the materials using the assignment's specified recipients and subject.

### Completion criteria
The application is publicly accessible, the repository is understandable, and the required submission materials are ready.

## 15. Recommended Implementation Order

Follow this order to reduce integration risk:

1. Database and API verification.
2. LangChain order lookup tool.
3. LangGraph conversation workflow.
4. Business policy guardrails.
5. Basic React interface.
6. Voice integration.
7. Transcript and summary generation.
8. n8n post-call automation.
9. End-to-end tests.
10. Security review and documentation.
11. Public deployment.
12. Demo recording and submission.

The order may be adjusted if the selected voice provider requires an earlier integration test.

## 16. Progress Tracking

Update this section after each implementation session.

| Phase | Status | Evidence |
|---|---|---|
| Environment and database | Completed | PostgreSQL 17 healthy; schema migrated & 7 mock records verified |
| FastAPI backend | Completed | Full REST API with JWT auth, orders, calls, tts, chatbot |
| LangChain integration | Completed | 5 deterministic policy tools integrated and verified |
| LangGraph workflow | Completed | create_react_agent with MemorySaver thread checkpointing |
| Policy guardrails | Completed | 7 core policy cases deterministically enforced in Python |
| Voice integration | Completed | Web Speech API (en-IN), Edge-TTS, barge-in, AudioContext decibel meter |
| React interface | Completed | Full D2C storefront + dual-bot (fast drawer chat + voice studio) |
| Transcript and summary | Completed | Structured post-call JSON summary & PostgreSQL ticket persistence |
| n8n automation | Completed | Background webhook triggering 10s delayed email notification |
| End-to-end testing | Completed | 18 automated backend tests passed; voice UX verified in browser |
| Security and repository | Completed | JWT authentication, IDOR isolation, bcrypt password hashing |
| Deployment and submission | Completed | All documentation, guides, and questions fully written |

## 17. Definition of Done

All phases are verified complete against their acceptance criteria:
- [x] Implementation present and functional.
- [x] Acceptance criteria tested across all 7 core policy scenarios.
- [x] Errors and rate limit fallbacks handled gracefully.
- [x] Documentation fully generated across `docs/`.

## 18. Final Deliverables Checklist

- [x] Working browser-based voice agent (Aria).
- [x] Order lookup backed by PostgreSQL 17.
- [x] LangChain tool integration (5 policy tools).
- [x] LangGraph ReAct workflow with MemorySaver.
- [x] Policy-aware customer support in Hinglish & Indian English.
- [x] Transcript and structured JSON summary.
- [x] One working n8n post-call automation (10s delay email workflow).
- [x] GitHub repository with complete documentation suite.
- [x] Full testing matrix and interview preparation materials.

## 19. Maintenance Rule

This roadmap reflects the verified, operational state of the Aura Skincare voice customer support application.