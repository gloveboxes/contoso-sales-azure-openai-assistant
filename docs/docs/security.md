# Security Concerns

## SQL Malicious Attacks

A common concern with the demo scenario is security, particularly the risks of SQL injection or malicious attempts to drop the database. While these concerns are valid, they can easily be mitigated by setting the database access rights. 

For SQLite, this involves configuring the database as read-only. For a Database Service such as Postgres or Azure SQL, you would assign the application a read-only (Select) role. Additionally, running the application in a secure environment provides an extra layer of protection.

In enterprise scenarios, data is extracted and transformed from transactional systems into a read-only database or data warehouse with a user friendly schema. This approach ensures the data is secure, optimized for performance, and that the application has read-only access to the data.

## Azure OpenAI Assistants API

It’s crucial to secure the Azure OpenAI resources used in the app with [Azure RBAC](https://learn.microsoft.com/training/modules/secure-azure-resources-with-rbac/). to prevent unauthorized access. Without proper security, anyone with access to the Azure OpenAI Assistants API could interact with the assistant and potentially gain access to sensitive data.
