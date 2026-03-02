# OPERATING PROCEDURES

1.  **Test After Implementation**: Every time a code module or feature is finished, you MUST perform a module test and verify functionality before proceeding.
2.  **Instruction Mode (Daily)**: Use the `rpa-driver` skill (ecw-bridge MCP) to navigate and interact with the EMR.
3.  **HIPAA Compliance**: NEVER send raw patient data to cloud models. Use `summarize_phi` tool first.
4.  **Human-in-the-Loop**: All orders must be reviewed in the dashboard queue before `pend_order` is called.
