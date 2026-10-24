# Aura Skincare Voice Agent — Project Requirements

## Document Information

| Field | Value |
|---|---|
| Project | Aura Skincare Voice Agent |
| AI agent | Aria |
| Document | Project Requirements / SRS |
| Version | 1.0 |
| Status | Initial draft |
| Primary purpose | AI-powered voice customer support |

## 1. Project Overview

Aria is a browser-based AI voice customer-support agent for Aura Skincare, a fictional direct-to-consumer (D2C) skincare brand.

The application enables customers to interact with an AI assistant through spoken conversation. Aria answers questions about orders, shipping, returns, cancellations, and other supported customer-service topics.

The agent retrieves order information from PostgreSQL using a dedicated tool, applies the brand's stated policies, and generates a conversation transcript and structured call summary after the interaction.

## 2. Problem Statement

Customers frequently need assistance with routine questions such as order status, tracking information, delivery estimates, return eligibility, and cancellation policies.

A voice-based AI assistant can make these interactions more natural and accessible while demonstrating automated information retrieval, conversational context management, and policy-aware responses.

The goal is to build a working prototype that demonstrates these capabilities without falsely claiming to perform actions that the system cannot execute.

## 3. Project Objectives

- Build a browser-based voice customer-support interface.
- Support spoken customer input and spoken AI responses.
- Retrieve order information through `get_order_details(order_id)`.
- Use PostgreSQL as the source of mock order data.
- Apply Aura's business policies to customer questions.
- Maintain relevant context during a call.
- Display a chronological transcript after the call.
- Generate a structured JSON call summary.
- Integrate LangChain and LangGraph into the AI agent workflow.
- Demonstrate one n8n post-call automation.
- Deploy the application publicly.
- Publish the source code and setup instructions in GitHub.
- Prepare the assignment's demo video and submission materials.

## 4. Scope

### 4.1 In scope

- Browser-based voice interaction.
- Call start and end controls.
- Listening, Thinking, and Speaking indicators.
- Order lookup using the supplied mock dataset.
- Policy-based customer-support responses.
- Missing and invalid order ID handling.
- Conversation transcript.
- Structured post-call summary.
- LangChain tool integration.
- LangGraph conversation workflow.
- One n8n post-call workflow.
- Local development, testing, and public deployment.
- Technical documentation.

### 4.2 Out of scope for the initial prototype

- Real payment processing.
- Real courier API integration.
- Actual refund execution.
- Actual cancellation against a live commerce platform.
- Production customer identity verification.
- Integration with a real D2C order-management system.
- Production-scale contact-centre infrastructure.

These capabilities may be considered future enhancements but must not be presented as existing functionality.

## 5. Users

### 5.1 Customer

A customer should be able to:
- Start and end a call.
- Ask questions naturally by voice.
- Check the status of a supported order.
- Obtain available tracking and delivery information.
- Ask questions about Aura's stated policies.
- Receive explanations when an action is not permitted.
- View the transcript and summary after the call.

### 5.2 Evaluator or developer

An evaluator should be able to:
- Test the application using the three mock orders.
- Observe the voice interaction states.
- Verify that the agent uses the order lookup tool.
- Test business-policy edge cases.
- Review the transcript and JSON summary.
- Inspect the repository and deployment.
- Understand the architecture and implementation decisions.

## 6. Functional Requirements

### FR-01: Voice interface

The application shall provide:
- A Start Call control.
- An End Call control.
- Microphone input.
- Spoken agent responses.
- Listening, Thinking, and Speaking indicators.
- Visible errors for microphone, network, or voice-service failures.

The selected voice implementation must be documented.

### FR-02: Conversation management

The agent shall:
- Understand common customer-support requests.
- Retain relevant context during the current call.
- Ask for an order ID when required and not already available.
- Avoid repeatedly asking for information already provided.
- Give concise and customer-friendly answers.
- Distinguish verified information from uncertainty.
- Avoid inventing order details, policy exceptions, or completed actions.

### FR-03: Order lookup

The backend shall implement the function:

`get_order_details(order_id)`

It shall:
- Validate that an order ID is supplied.
- Normalize the order ID where appropriate.
- Retrieve the order from PostgreSQL.
- Return structured information for a valid order.
- Handle unknown order IDs.
- Handle database failures without exposing sensitive internal details to customers.

The AI agent must use this tool when it needs verified order information rather than guessing.

### FR-04: Assignment mock orders

The initial dataset contains the following records.

| Order ID | Customer | Product | Amount | Status |
|---|---|---|---:|---|
| ORD-101 | Priya Sharma | Vitamin C Serum (30ml) | ₹699 | Out for Delivery |
| ORD-102 | Rahul Verma | Hydrating Sunscreen SPF 50 | ₹499 | Delivered |
| ORD-103 | Ananya Patel | Green Tea Face Wash + Toner | ₹850 | Processing |

Additional order information:

**ORD-101**
- Courier: BlueDart.
- Tracking number: BD-982103.
- Expected delivery: by 6 PM today.

**ORD-102**
- Courier: Delhivery.
- Tracking number: DL-441029.
- Delivered 14 days ago.

**ORD-103**
- Ordered three hours ago.
- Status: Processing.
- Eligible for cancellation according to the assignment's current status-based policy.

The dataset is mock data. These records do not represent live orders or real courier tracking.

### FR-05: Shipping policy

The agent shall explain:
- Free shipping applies to orders above ₹499.
- A ₹50 shipping fee applies to orders below ₹499.
- The assignment does not explicitly specify the shipping fee for an order of exactly ₹499.

The agent must not invent a policy for the unresolved boundary case.

### FR-06: Delivery policy

Standard delivery takes 3–5 business days.

The agent must distinguish the general delivery estimate from the specific delivery estimate stored for an order.

### FR-07: Return policy

Returns are permitted:
- Within seven days of delivery.
- Only for products that are unopened and unused.
- Only when the products remain in their original packaging.

For ORD-102, which was delivered 14 days ago, the agent must explain that the standard return window has passed.

### FR-08: Damaged or defective products

Customers must report damaged or defective products within 48 hours and provide photos for a replacement request.

The prototype may explain the procedure but must not claim that a replacement has been approved or created unless a corresponding capability is implemented.

### FR-09: Cancellation policy

Cancellation is allowed while an order is Processing.

Cancellation is not allowed after the order becomes Shipped or Out for Delivery.

The initial prototype can explain cancellation eligibility. Unless a cancellation operation is explicitly implemented and confirmed, the agent must not claim that it has cancelled an order.

### FR-10: Cash on Delivery

The stated COD policy permits orders up to ₹2,500, with cash or UPI as payment methods.

The agent shall explain this policy accurately when relevant.

### FR-11: Transcript

After a call, the application shall display a chronological transcript of the interaction.

Where supported, the transcript should distinguish customer speech from agent speech.

### FR-12: Call summary

The application shall generate a structured JSON summary containing:

- `customer_intent`
- `order_id`
- `resolution_status`
- `call_summary`

The summary must reflect the actual conversation and its outcome.

### FR-13: Post-call automation

The planned system shall trigger one n8n workflow after a call to process or store its summary.

The workflow's exact trigger, destination, authentication, and error-handling behavior will be defined during implementation.

### FR-14: Test order helper

The user interface shall provide a visible way to test the supplied mock orders, making the assignment easy to demonstrate.

## 7. Technical Requirements

| Component | Planned technology |
|---|---|
| Frontend | React + Vite |
| Backend | Python + FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| PostgreSQL driver | psycopg |
| LLM and tool integration | LangChain |
| Stateful agent workflow | LangGraph |
| Voice integration | Browser-compatible voice solution to be selected |
| Post-call automation | n8n |
| Local database environment | Docker Compose |
| Source control | Git and GitHub |

The selected voice provider, LLM provider, model, and deployment services must be recorded once finalized.

## 8. Non-Functional Requirements

### Usability
- The interface should be straightforward to operate.
- Call state must be visible.
- Responses should be concise and understandable.

### Performance
- Voice interactions should have reasonable latency.
- Tool calls should not leave the interface permanently in a Thinking state.
- Errors and timeouts should be handled gracefully.

### Reliability
- Invalid order IDs must not crash the application.
- Database and voice-service failures must be handled.
- Summaries must not invent resolutions.

### Security
- Secret API keys must remain on the backend.
- `.env` files must not be committed to Git.
- PostgreSQL must not be exposed publicly without an explicit security design.
- Public endpoints must not disclose internal stack traces or credentials.

### Maintainability
- Frontend, backend, data models, tools, and agent workflow must have clear module boundaries.
- Setup instructions must be documented.
- Core functionality must be testable without requiring a live voice call.

## 9. Acceptance Criteria

- [ ] The backend connects to PostgreSQL.
- [ ] All three mock orders are stored and retrievable.
- [ ] The order lookup tool handles valid, missing, and unknown IDs.
- [ ] The browser interface supports starting and ending calls.
- [ ] Listening, Thinking, and Speaking indicators work.
- [ ] The agent follows the specified business policies.
- [ ] The agent does not invent order information.
- [ ] The transcript is displayed after a call.
- [ ] The required JSON summary is generated.
- [ ] The n8n post-call workflow is demonstrated.
- [ ] The application is publicly deployed.
- [ ] The GitHub README explains architecture and setup.
- [ ] The requested 3–5 minute demo video is prepared.
- [ ] The assignment submission email and required materials are prepared.

## 10. Current Implementation Status

Verified:
- PostgreSQL runs locally in Docker.
- The Python database connection works.
- The `orders` table exists.
- The three assignment mock orders are stored in PostgreSQL.
- The basic FastAPI order lookup has been tested successfully.

Not yet verified as complete:
- LangChain tool integration.
- LangGraph workflow.
- Browser voice integration.
- Transcript and summary UI.
- n8n automation.
- Public deployment.

## 11. Constraints and Assumptions

- The supplied assignment defines the mock order records and business policies.
- Mock records are used instead of a live commerce database.
- Any additional architecture or security decisions are implementation choices.
- Unspecified policy behavior must remain explicitly unresolved until clarified.
- Requirements should only be marked complete after testing.

## 12. Definition of Done

A feature is complete when:
1. Its expected behavior is documented.
2. The implementation is present.
3. Its normal and relevant error paths are tested.
4. The observed result matches the requirement.
5. Any limitations