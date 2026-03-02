# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Amazon Bedrock AgentCore Code Interpreter MCP Server."""

import os
from .tools import execution, files, session
from .utils import aws_client
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from loguru import logger
from mcp.server.fastmcp import FastMCP


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[dict]:
    """Server lifespan handler for startup and shutdown cleanup."""
    # Startup — nothing to do
    yield {}
    # Shutdown — stop sessions if configured, then clear client cache
    auto_stop = os.environ.get('AUTO_STOP_SESSIONS', 'false').lower() == 'true'
    if auto_stop:
        logger.info('AUTO_STOP_SESSIONS enabled, stopping all active sessions')
        await aws_client.stop_all_sessions()
    else:
        aws_client.clear_clients()


APP_NAME = 'amazon-bedrock-agentcore-code-interpreter-mcp-server'

mcp = FastMCP(
    APP_NAME,
    instructions=(
        'This server provides tools for Amazon Bedrock AgentCore Code Interpreter. '
        'Use start_code_interpreter_session to create a sandbox, then execute_code, '
        'execute_command, or install_packages to run code. Use upload_file and '
        'download_file to transfer data. Stop sessions when done to release resources.'
    ),
    lifespan=lifespan,
)

# Session lifecycle tools
mcp.tool()(session.start_code_interpreter_session)
mcp.tool()(session.stop_code_interpreter_session)
mcp.tool()(session.get_code_interpreter_session)
mcp.tool()(session.list_code_interpreter_sessions)

# Code execution tools
mcp.tool()(execution.execute_code)
mcp.tool()(execution.execute_command)
mcp.tool()(execution.install_packages)

# File operation tools
mcp.tool()(files.upload_file)
mcp.tool()(files.download_file)


def main() -> None:
    """Main entry point for the MCP server."""
    mcp.run()


if __name__ == '__main__':
    main()
