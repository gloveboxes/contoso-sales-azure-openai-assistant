# Frequently asked questions

## Security Concerns

A common concern with the demo scenario is security, particularly the risks of SQL injection or malicious attempts to drop the database. While these concerns are valid, they can be mitigated by setting the database to read-only mode. For SQLite, this involves configuring the database as read-only. For a Database Service, you would assign the application a read-only (Select) role. Additionally, running the application in a secure environment provides an extra layer of protection.

In enterprise scenarios, data is extracted and transformed from transactional systems into a read-only database or data warehouse. This approach ensures the data is secure, optimized for performance, and that the application has read-only access to the data.
