Stretch: show that any framework can use PASSPORT. Build `integrations/langgraph_example/` (separate requirements.txt; do NOT add LangChain to backend/requirements.txt).

Use verify-before-use: read the installed langgraph/langchain docs for the versions you install. Plan first, wait for my OK.

A tiny LangGraph agent with two fake tools whose tool node calls `POST /v1/decide` (backend URL from env) before executing each tool call, passing the user request and prior tool outputs as untrusted context. On DENY, return the reason as the tool message. README with a 10-line snippet showing the integration. This answers "where's LangChain?" honestly: the gate is framework-agnostic.
