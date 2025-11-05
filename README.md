#  Canvas API Chatbot (Hybrid Design)

##  Overview
This project is a **Canvas API Chatbot** built in **Python** that allows users to interact with their Canvas LMS data through a simple command-line or future UI interface.  
It uses a **hybrid design**, meaning each user provides their own **Canvas API access token** and **instance URL** — ensuring privacy and security.

The chatbot will eventually support:
- Authentication using user-provided API credentials  
- Fetching data such as courses, assignments, and grades  
- Conversational or menu-based interaction with the data  

---

##  Current Development Phase
**Phase 1 – Authentication**

**Goal:**  
- Prompt the user for their Canvas instance URL and API token  
- Validate authentication by fetching `/api/v1/users/self`  
- Print the authenticated user’s name or Canvas ID as confirmation  

 *Once complete, the app will confirm a successful connection to Canvas.*

---

##  Planned Phases

| Phase | Description | Status |
|:------|:-------------|:-------|
| 1 | Authentication (API token input + validation) |  In Progress |
| 2 | Data Fetching (courses, assignments, grades) |  Next |
| 3 | Logical Interface (CLI / chatbot interaction) |  Planned |

---

##  Requirements
- Python 3.11+  
- `requests` library  

Install dependencies:
```bash
pip install requests
