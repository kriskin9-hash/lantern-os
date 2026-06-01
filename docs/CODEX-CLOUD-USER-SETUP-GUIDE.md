# Codex Cloud User Setup Guide

Generated: 2026-05-28
Target Users: gage, courtney, waruichinchilla

## Overview

This guide enables cloud-first access to Lantern OS chat and RAG models via Codex Cloud environment.

## Prerequisites

- Active Codex Cloud account
- GitHub account (for private repo access)
- Lantern OS GitHub repository access (operator will grant)

## Setup Steps

### Step 1: Access Codex Cloud Environment Settings

Navigate to:
```
https://chatgpt.com/codex/cloud/settings/environment/create
```

### Step 2: Configure GitHub Connector

1. Select "GitHub" as the connector type
2. Authorize Codex Cloud to access your GitHub account
3. Select the repositories:
   - `alex-place/lantern-os` (primary)
   - `alex-place/gamemaker-room-editor` (GameMaker development)
   - `alex-place/ChildOfLevistus` (GameMaker game project)
4. Choose repository access level (read-only recommended for users)
5. Create the environment

### Step 3: Configure User-Specific Environment

For each user, configure the following environment variables:

**Additional Repository Access:**
All users get access to:
- `alex-place/lantern-os` (primary)
- `alex-place/gamemaker-room-editor` (GameMaker development tools)
- `alex-place/ChildOfLevistus` (GameMaker game project)

#### Gage (Educational Focus)
```json
{
  "LANCERN_USER": "gage",
  "LANCERN_USER_ROLE": "educational",
  "LANCERN_CONTENT_FILTER": "family_safe",
  "LANCERN_RAG_CONTEXT": ["art_education", "learning_projects", "family_activities"]
}
```

#### Courtney (Collaboration Focus)
```json
{
  "LANCERN_USER": "courtney", 
  "LANCERN_USER_ROLE": "collaborator",
  "LANCERN_CONTENT_FILTER": "family_safe",
  "LANCERN_RAG_CONTEXT": ["family_projects", "collaboration_workflows", "shared_decisions"]
}
```

#### Waruichinchilla (External Collaborator)
```json
{
  "LANCERN_USER": "waruichinchilla",
  "LANCERN_USER_ROLE": "external_collaborator",
  "LANCERN_CONTENT_FILTER": "project_scoped",
  "LANCERN_RAG_CONTEXT": ["technical_collaboration", "project_documentation", "shared_workflows", "gamemaker_development"]
}
```

### Step 4: Verify Access

Test your Codex Cloud environment by asking:
```
"Show me my user context in the Lantern OS RAG system"
```

Expected response should include your user profile and relevant context.

## GameMaker Repository Access

### Available Projects

Users now have access to GameMaker development projects:

1. **gamemaker-room-editor**: GameMaker room development tools and utilities
2. **ChildOfLevistus**: GameMaker game project source and validation lane

### Access Levels

- **Gage**: Read-only access for educational game development learning
- **Courtney**: Read-only access for family game project collaboration
- **Waruichinchilla**: Read-only access for technical game development collaboration

### Usage Examples

```
"Show me the structure of the ChildOfLevistus game project"
"Explain how the gamemaker-room-editor tools work"
"Help me understand GameMaker development patterns"
"What are the key components of the room editor?"
```

## Chat Interface Access

### Discord Lounge Bot

Once configured, users can access Lantern OS chat via Discord:

1. Join the designated Lantern Discord server
2. Use the `!lantern-status` command to check system status
3. Interact with the bot in allowlisted channels

### Lantern Garage Web App

Local web interface access (operator-hosted):
```
http://127.0.0.1:4177
```

Features:
- User-aware sessions
- RAG context retrieval
- Project collaboration tools
- Status dashboards

## RAG Context Access

Your user profile is now part of the Lantern OS RAG system:

### Gage's RAG Context
- Art education materials
- School project support  
- Family learning activities
- Age-appropriate content filtering

### Courtney's RAG Context
- Family project collaboration
- Shared decision making workflows
- Family-safe content access
- Collaboration tools

### Waruichinchilla's RAG Context
- Technical collaboration workflows
- Project-specific documentation
- Shared work processes
- Project-scoped content access

## Safety and Privacy

### Content Filtering
- All users have content filtering appropriate to their role
- Family-safe filtering for gage and courtney
- Project-scoped filtering for waruichinchilla

### Data Privacy
- No personal credentials stored in RAG cache
- User profiles contain context only, no private data
- Operator controls repository access levels

### Access Boundaries
- Read-only repository access recommended for users
- No destructive actions available through chat interface
- Sensitive configuration requires operator approval

## Troubleshooting

### Issue: Repository Access Denied
**Solution**: Contact operator to grant GitHub repository access

### Issue: User Context Not Loading
**Solution**: Verify environment variables are set correctly in Codex Cloud

### Issue: Discord Bot Not Responding
**Solution**: Check with operator that bot is running and you're in correct channel

### Issue: Content Filter Too Restrictive
**Solution**: Discuss with operator to adjust filter settings for your use case

## Next Steps

1. Complete Codex Cloud environment setup
2. Test chat interface access
3. Verify RAG context loading
4. Provide feedback to operator on user experience

## Support

For setup issues or access problems, contact the Lantern OS operator.