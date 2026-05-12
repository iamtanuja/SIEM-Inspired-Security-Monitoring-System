Security Monitoring System (SIEM-Inspired)
Overview
This project is a SIEM-inspired security monitoring web application built using Flask and SQLite. It simulates basic security operations such as activity logging, access control, threat detection, and alert generation.
Project Flow
1. User Authentication
Users register and log in to the system
Login attempts are tracked for security monitoring
2. Activity Logging
System records user actions such as:
Login attempts
Page access
Logs are stored for monitoring and analysis
3. Role-Based Access Control (RBAC)
Users are assigned roles
Access to system features is restricted based on role permissions
4. Threat Detection & Alerts
System detects suspicious activities such as:
Multiple failed login attempts
Abnormal behavior patterns
Generates alerts with severity levels:
Low
Medium
High
Critical
5. Account Protection
Account is temporarily locked after repeated failed login attempts
Simulates brute-force attack prevention
6. Risk-Based Analysis
User behavior is analyzed to identify anomalies
Security response is triggered based on risk level
Tech Stack
Flask (Backend)
SQLite (Database)
HTML/CSS (Frontend)
