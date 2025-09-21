## Inspiration

Banking reimagined for the digital age. We wanted to eliminate the frustration of waiting in lines and limited banking hours by creating a bank that's open 24/7 with AI employees ready to help instantly. The inspiration came from transforming the classic Bank of Anthos into a next-generation, AI-powered banking experience.

## What it does

AI-powered banking platform provides two main AI agents that work together:

**Customer Service AI Agent**: Users can chat with an AI assistant to check balances, send money, manage contacts, and get information about promotions they're eligible for.

**Promotion Management AI Agent**: Automatically creates custom promotions (like "get a bonus when you deposit $1000"), monitors user transactions to check qualification, and automatically credits rewards to accounts when users meet promotion criteria.

## How we built it

- **Google Agent Development Kit (ADK)** with Gemini 2.5 Flash model for conversational AI
- **Agent-to-Agent (A2A) Protocol** allowing our CS and Promotion agents to communicate
- **Model Context Protocol (MCP)** to standardize banking actions as tools that AI agents can use
- **Google Kubernetes Engine (GKE)** for cloud deployment and scaling
- **Vertex AI** the brain behind the agents, the Gemini LLM provider
- **NATS messaging** for event-driven transaction notifications
- **FastAPI** for web service implementation

## Challenges we ran into

- **Debugging complexity**: When things went wrong with the Google ADK, debugging was challenging due to limited documentation. I had to read the open-source code directly to troubleshoot issues.
- **ADK is bleeding edge**: The version that I first used has bug in it, only after digging through Github issues I found out about the cryptic errors that I get and upgraded the version (the new version release was Sep 15, which is during the hackathon period!)
- **Container registry requirements**: Moving from local development (using kind) to GKE required hosting all container images in a registry, unlike local builds.

## Accomplishments that we're proud of

- **Seamless cloud deployment**: Successfully transitioned from local development to GKE with minimal friction
- **New tools never used before**: ADK, A2A, Vertex AI and GKE are all new to me. But they are easy to get started with
- **Agent-to-agent communication**: Implemented AI agents that can communicate and delegate tasks to each other
- **Real-time promotion checking system**: Built an event-driven system that automatically detects and rewards qualifying transactions with AI agent as the logic
- **Standardized AI tools**: Created a robust MCP integration that makes banking actions accessible to AI agents

## What we learned

- **Observability needs**: I learned that logging, traceability, and observability are essential for Kubernetes deployments, as debugging and monitoring become extremely difficult without them.
- **Bleeding edge framework**: Using bleeding edge framework is fun, but it can be a major blocker when something doesn't work as expected. Fortunately, the bug was fixed in a new release just one week before the submission.

## What's next for Meet Your AI Bankers: Next-Gen Bank with AI Employees!

- **Enhanced AI capabilities**: Expand the range of banking services the AI agents can handle, such as home loan application
- **Auth & Security**: Authentication and session managements are very minimal
- **Advanced promotion engine**: Implement more sophisticated promotion logic and personalized offers
- **Multi-channel support**: Extend beyond chat to voice and mobile app integration
- **Improved observability**: Implement comprehensive monitoring and analytics dashboards
- **Security enhancements**: Add advanced fraud detection and security features
- **Integration expansion**: Connect with more external banking services and APIs