# Amazon Bedrock AgentCore Code Interpreter MCP Server

Model Context Protocol (MCP) server for secure code execution via Amazon Bedrock AgentCore.

## Features

- **9 code interpreter tools** — session lifecycle, code execution, and file operations
- **Multi-language execution** — run Python, JavaScript, or TypeScript in sandboxed sessions
- **Shell access** — execute arbitrary shell commands and install pip packages
- **File transfer** — upload data into sessions and download results (binary files base64-encoded)
- **Cloud-native sessions** — sessions run in isolated sandboxes via AgentCore with standard IAM authentication

## Prerequisites

### Installation Requirements

1. Install `uv` from [Astral](https://docs.astral.sh/uv/getting-started/installation/) or the [GitHub README](https://github.com/astral-sh/uv#installation)
2. Install Python 3.10 or newer using `uv python install 3.10` (or a more recent version)
3. AWS credentials configured (via environment variables, profile, or IAM role)
4. Access to Amazon Bedrock AgentCore Code Interpreter APIs

## Installation

Configure the MCP server in your MCP client configuration.

| Kiro | Cursor | VS Code |
|:----:|:------:|:-------:|
| [![Add to Kiro](https://kiro.dev/images/add-to-kiro.svg)](https://kiro.dev/launch/mcp/add?name=awslabs.amazon-bedrock-agentcore-code-interpreter-mcp-server&config=%7B%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22awslabs.amazon-bedrock-agentcore-code-interpreter-mcp-server%40latest%22%5D%2C%22env%22%3A%7B%22AWS_PROFILE%22%3A%22your-aws-profile%22%2C%22AWS_REGION%22%3A%22us-east-1%22%2C%22FASTMCP_LOG_LEVEL%22%3A%22ERROR%22%7D%7D) | [![Install MCP Server](https://cursor.com/deeplink/mcp-install-light.svg)](https://cursor.com/en/install-mcp?name=awslabs.amazon-bedrock-agentcore-code-interpreter-mcp-server&config=eyJjb21tYW5kIjoidXZ4IGF3c2xhYnMuYW1hem9uLWJlZHJvY2stYWdlbnRjb3JlLWNvZGUtaW50ZXJwcmV0ZXItbWNwLXNlcnZlckBsYXRlc3QiLCJlbnYiOnsiQVdTX1BST0ZJTEUiOiJ5b3VyLWF3cy1wcm9maWxlIiwiQVdTX1JFR0lPTiI6InVzLWVhc3QtMSIsIkZBU1RNQ1BfTE9HX0xFVkVMIjoiRVJST1IifX0=) | [![Install on VS Code](https://img.shields.io/badge/Install_on-VS_Code-FF9900?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=Amazon%20Bedrock%20AgentCore%20Code%20Interpreter%20MCP%20Server&config=%7B%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22awslabs.amazon-bedrock-agentcore-code-interpreter-mcp-server%40latest%22%5D%2C%22env%22%3A%7B%22AWS_PROFILE%22%3A%22default%22%2C%22AWS_REGION%22%3A%22us-east-1%22%2C%22FASTMCP_LOG_LEVEL%22%3A%22ERROR%22%7D%2C%22disabled%22%3Afalse%2C%22autoApprove%22%3A%5B%5D%7D) |

### Command Line

Run the server directly using `uvx` (no install required):

```bash
uvx awslabs.amazon-bedrock-agentcore-code-interpreter-mcp-server@latest
```

Or from a local source checkout (for development):

```bash
uv run --directory /path/to/amazon-bedrock-agentcore-code-interpreter-mcp-server \
  awslabs.amazon-bedrock-agentcore-code-interpreter-mcp-server
```

Set environment variables as needed (see [Environment Variables](#environment-variables)):

```bash
AWS_REGION=us-east-1 AWS_PROFILE=your-profile \
  uvx awslabs.amazon-bedrock-agentcore-code-interpreter-mcp-server@latest
```

The server uses stdio transport. Any MCP client that supports stdio can use the commands above — configure the command and args in your client's MCP server settings.

### Claude Desktop

Example configuration for Claude Desktop (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "amazon-bedrock-agentcore-code-interpreter-mcp-server": {
      "command": "uvx",
      "args": ["awslabs.amazon-bedrock-agentcore-code-interpreter-mcp-server@latest"],
      "env": {
        "AWS_REGION": "us-east-1",
        "AWS_PROFILE": "your-profile"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

### Windows Installation

For Windows users, the MCP server configuration format is slightly different:

```json
{
  "mcpServers": {
    "amazon-bedrock-agentcore-code-interpreter-mcp-server": {
      "disabled": false,
      "timeout": 60,
      "type": "stdio",
      "command": "uv",
      "args": [
        "tool",
        "run",
        "--from",
        "awslabs.amazon-bedrock-agentcore-code-interpreter-mcp-server@latest",
        "awslabs.amazon-bedrock-agentcore-code-interpreter-mcp-server.exe"
      ],
      "env": {
        "AWS_REGION": "us-east-1",
        "AWS_PROFILE": "your-profile"
      }
    }
  }
}
```

Or using Docker after a successful `docker build -t mcp/bedrock-agentcore-code-interpreter .`:

```json
{
  "mcpServers": {
    "amazon-bedrock-agentcore-code-interpreter-mcp-server": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "--interactive",
        "--env", "AWS_REGION=us-east-1",
        "--env", "AWS_PROFILE=your-profile",
        "mcp/bedrock-agentcore-code-interpreter:latest"
      ],
      "env": {},
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

## Basic Usage

1. Start a session with `start_code_interpreter_session`
2. Upload data with `upload_file` if needed
3. Install dependencies with `install_packages` (e.g., `["numpy", "pandas"]`)
4. Run code with `execute_code` or shell commands with `execute_command`
5. Download results with `download_file`
6. Stop the session with `stop_code_interpreter_session` when done

Example conversation:

> "Install pandas, upload this CSV, and compute summary statistics"
>
> The agent calls `start_code_interpreter_session`, then `install_packages(packages=["pandas"])`,
> then `upload_file(path="data.csv", content="...")`, then `execute_code(code="import pandas as pd; df = pd.read_csv('data.csv'); print(df.describe())")`,
> and returns the statistics from stdout.

## Tools

### Session Lifecycle (4 tools)

#### start_code_interpreter_session

Create a new sandboxed code interpreter session.

```python
start_code_interpreter_session(
    code_interpreter_identifier: str | None = None,
    name: str | None = None,
    session_timeout_seconds: int = 900,
    region: str | None = None,
) -> CodeInterpreterSessionResponse
```

**Parameters:**
- `code_interpreter_identifier`: Code interpreter to use (default: `aws.codeinterpreter.v1`)
- `name`: Human-readable session name
- `session_timeout_seconds`: Session timeout in seconds (default: 900)
- `region`: AWS region override (default: from `AWS_REGION` environment variable)

**Returns:** Session ID, status, code interpreter identifier, message.

#### stop_code_interpreter_session

Stop a running session and release its resources.

```python
stop_code_interpreter_session(
    session_id: str,
    code_interpreter_identifier: str | None = None,
    region: str | None = None,
) -> CodeInterpreterSessionResponse
```

**Parameters:**
- `session_id`: Session to stop (required)
- `code_interpreter_identifier`: Code interpreter identifier (default: `aws.codeinterpreter.v1`)
- `region`: AWS region override

**Returns:** Session ID, status, code interpreter identifier, message.

#### get_code_interpreter_session

Get the status and details of a specific session.

```python
get_code_interpreter_session(
    session_id: str,
    code_interpreter_identifier: str | None = None,
    region: str | None = None,
) -> CodeInterpreterSessionResponse
```

#### list_code_interpreter_sessions

List code interpreter sessions with optional filtering.

```python
list_code_interpreter_sessions(
    code_interpreter_identifier: str | None = None,
    status: str | None = None,
    max_results: int | None = None,
    next_token: str | None = None,
    region: str | None = None,
) -> SessionListResponse
```

**Parameters:**
- `status`: Filter by session status (`READY` or `TERMINATED`)
- `max_results`: Maximum number of results (1–100)
- `next_token`: Pagination token from a previous response
- `region`: AWS region override

**Returns:** List of sessions (session ID, status, name), optional next token, message.

### Code Execution (3 tools)

#### execute_code

Execute code in a session. Supports Python, JavaScript, and TypeScript.

```python
execute_code(
    session_id: str,
    code: str,
    language: str = "python",
    clear_context: bool = False,
    region: str | None = None,
) -> ExecutionResult
```

**Parameters:**
- `session_id`: Session to execute in (required)
- `code`: Source code to execute (required)
- `language`: Programming language — `"python"`, `"javascript"`, or `"typescript"` (default: `"python"`)
- `clear_context`: Reset execution context before running (default: false)
- `region`: AWS region override

**Returns:** stdout, stderr, exit code, error flag, additional content, message.

#### execute_command

Execute a shell command in a session.

```python
execute_command(
    session_id: str,
    command: str,
    region: str | None = None,
) -> ExecutionResult
```

**Parameters:**
- `session_id`: Session to execute in (required)
- `command`: Shell command to execute (required)
- `region`: AWS region override

**Returns:** stdout, stderr, exit code, error flag, message.

#### install_packages

Install Python packages via pip in a session.

```python
install_packages(
    session_id: str,
    packages: list[str],
    upgrade: bool = False,
    region: str | None = None,
) -> ExecutionResult
```

**Parameters:**
- `session_id`: Session to install in (required)
- `packages`: Package names with optional version specifiers (e.g., `["numpy", "pandas>=2.0"]`) (required)
- `upgrade`: Upgrade packages to latest version (default: false)
- `region`: AWS region override

**Returns:** stdout, stderr, exit code, error flag, message.

### File Operations (2 tools)

#### upload_file

Upload a file into a session's sandbox filesystem.

```python
upload_file(
    session_id: str,
    path: str,
    content: str,
    description: str | None = None,
    region: str | None = None,
) -> FileOperationResult
```

**Parameters:**
- `session_id`: Session to upload to (required)
- `path`: Relative file path, e.g. `"data/input.csv"` (required). Must not start with `/`.
- `content`: File content to upload (required)
- `description`: Description for LLM context
- `region`: AWS region override

**Returns:** File path, error flag, message.

#### download_file

Download a file from a session's sandbox. Binary files are automatically base64-encoded.

```python
download_file(
    session_id: str,
    path: str,
    region: str | None = None,
) -> FileOperationResult
```

**Parameters:**
- `session_id`: Session to download from (required)
- `path`: Relative file path, e.g. `"output/result.csv"` (required)
- `region`: AWS region override

**Returns:** File path, file content (base64-encoded if binary), error flag, message.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_REGION` | AWS region for AgentCore APIs | `us-east-1` |
| `AWS_PROFILE` | AWS CLI profile name | (default profile) |
| `CODE_INTERPRETER_IDENTIFIER` | AgentCore code interpreter resource ID | `aws.codeinterpreter.v1` |
| `AUTO_STOP_SESSIONS` | Stop all active sessions on server shutdown | `false` |
| `FASTMCP_LOG_LEVEL` | Log level for the MCP server (FastMCP framework) | `WARNING` |

## License

Apache-2.0. See [LICENSE](LICENSE).
