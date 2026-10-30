# Facts

Every number, incident, paper or claim about another organisation used on screen, in the pitch or in a judge answer must be here first, with a source. Use `/research` to add one. **Measured project numbers live in RESULTS.md, not here.**

## Confirmed (read on 2026-10-30)
| ID | Fact | Source | Confidence |
|---|---|---|---|
| F1 | OWASP Top 10 for LLM Applications 2025 ranks Prompt Injection #1 (LLM01) and lists Excessive Agency as LLM06. | https://www.invicti.com/blog/web-security/owasp-top-10-risks-llm-security-2025 (summary of the OWASP list; check genai.owasp.org before slides) | reputable |
| F2 | Invariant Labs (1 Apr 2025) showed MCP "tool poisoning": hidden instructions in a tool description made Cursor read `~/.ssh/id_rsa` and pass it in a hidden argument; also rug pulls and tool shadowing. | https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks | official (vendor research) |
| F3 | EchoLeak (CVE-2025-32711): zero-click data exfiltration from Microsoft 365 Copilot through a crafted email; patched. | https://thehackernews.com/2025/06/zero-click-ai-vulnerability-exposes.html | reputable |
| F4 | CaMeL (Google DeepMind et al., 2025) defends agents by separating trusted control flow from untrusted data with capabilities; reported 77% of AgentDojo tasks solved with provable security vs 84% undefended. | https://huggingface.co/papers/2503.18813 , https://arxiv.org/abs/2503.18813 | official (paper) |
| F5 | FIDES (Microsoft) attaches integrity/confidentiality labels to content and checks them deterministically before tool calls; shipped as middleware in Microsoft Agent Framework (Python). | https://learn.microsoft.com/en-us/agent-framework/agents/security , https://arxiv.org/abs/2505.23643 | official |
| F6 | PACT (2026) argues injection is dangerous when untrusted data binds an "authority-bearing argument" and enforces per-argument provenance contracts. | https://www.alphaxiv.org/abs/2605.11039 | paper |
| F7 | On 9 Oct 2025 NPCI, Razorpay and OpenAI announced an "Agentic Payments" pilot letting users buy inside ChatGPT with UPI, using UPI Reserve Pay so users pre-authorise an AI assistant within set limits. | https://razorpay.com/newsroom/?p=4631 , https://www.mitsloanme.com/?p=9172 | reputable |
| F8 | I4C data: about ₹19,813 crore lost and 21.77 lakh cheating complaints on the National Cyber Crime Reporting Portal in 2025. | https://ianslive.in/indians-lose-over-rs-52976-crore-to-cyber-frauds-over-six-years-report--20260103154943 | reputable (news citing I4C) |
| F9 | Simon Willison's "lethal trifecta": private data + exposure to untrusted content + a way to send data out makes an agent exploitable. | https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/ (page didn't load for us; open it before quoting) | reputable, quote not checked |

## Not yet confirmed (don't use these yet)
| ID | Claim | What's missing |
|---|---|---|
| U1 | MCPTox attack-success percentages | read arXiv 2508.14925 itself |
| U2 | "Clinejection" (Feb 2026) details | read the CSA note |
| U3 | Anything from the earlier ChatGPT research doc (TBIVL, CrowdStrike "ward", NIST wording) | no source found |
