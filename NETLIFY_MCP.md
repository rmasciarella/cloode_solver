# Netlify MCP Server Integration

This project includes integration with the Netlify MCP Server, which enables AI agents to manage Netlify deployments using natural language prompts.

## Overview

The Netlify MCP Server follows the Model Context Protocol (MCP) to provide API access and CLI tools for managing Netlify resources. This allows AI agents to:

- Create, manage, and deploy Netlify projects
- Modify access controls for enhanced project security
- Install or uninstall Netlify extensions
- Fetch user and team information
- Enable and manage form submissions
- Create and manage environment variables and secrets

## Prerequisites

✅ **Node.js 22 or higher** - Current version: `v22.16.0`  
✅ **Netlify account** - Required for deployment  
✅ **MCP client** - Claude Code supports MCP

## Configuration

The MCP configuration is located in `.mcp-config.json`:

```json
{
  "mcpServers": {
    "netlify": {
      "command": "npx",
      "args": [
        "-y",
        "@netlify/mcp"
      ]
    }
  }
}
```

## Usage with Claude Code

With the Netlify MCP Server configured, you can use natural language commands like:

- "Deploy the current project to Netlify"
- "Create a new Netlify site for this project"
- "Check the deployment status"
- "Update environment variables for the site"
- "Enable form submissions on the site"

## Troubleshooting

### Authentication Issues

If you encounter authentication problems, temporarily add a Netlify Personal Access Token (PAT):

1. Go to [Netlify Dashboard](https://app.netlify.com) > User settings > OAuth > New access token
2. Copy the token
3. Add to `.mcp-config.json`:

```json
{
  "mcpServers": {
    "netlify": {
      "command": "npx",
      "args": ["-y", "@netlify/mcp"],
      "env": {
        "NETLIFY_PERSONAL_ACCESS_TOKEN": "YOUR-PAT-VALUE"
      }
    }
  }
}
```

**⚠️ Security Warning**: Never commit your PAT to the repository! Remove it from config once authentication issues are resolved.

### Global Netlify CLI

For the best experience, install the Netlify CLI globally:

```bash
npm install -g netlify-cli
```

## Resources

- [Model Context Protocol Documentation](https://modelcontextprotocol.io)
- [Netlify MCP Server](https://www.npmjs.com/package/@netlify/mcp)
- [Netlify CLI Documentation](https://docs.netlify.com/cli/get-started/)