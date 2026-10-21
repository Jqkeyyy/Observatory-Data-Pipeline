# Observatory Frontend

Quick setup guide for running the server, database, and frontend.

## Prerequisites

Make sure you have the following installed:
- [Node.js](https://nodejs.org/en/download) (LTS)
- [Docker](https://www.docker.com/get-started/)
- [Python 3](https://www.python.org/downloads/)

---

## Getting Started

### 1. Open Docker Desktop
Make sure Docker Desktop is running on your machine.

### 2. Verify Python and pip are installed
Run these commands in your terminal to confirm Python and pip are installed:

    python3 --version
    pip3 --version

### 3. Clone the repository
Run this command in your terminal:

    git clone https://github.com/Jqkeyyy/Observatory-Data-Pipeline.git

### 4. Enter the project directory
Run this command:

    cd Observatory-Data-Pipeline

### 5. Add the `.env` file
- Go to Discord and open the `#envs` channel.
- Download the `.env` file (or create one and paste the contents).
- Place it inside the backend directory so the exact file path is:
  `Observatory-Data-Pipeline/backend/.env`

### 6. Run the development script
Run this command:

    python3 dev.py

---

## Troubleshooting

If something isn't working:
1. Open your browser's developer tools (Right-click anywhere on the page and click **Inspect**).
2. Go to the **Network** tab at the top.
3. Take a screenshot of the failing requests and share it in Discord for debugging help.