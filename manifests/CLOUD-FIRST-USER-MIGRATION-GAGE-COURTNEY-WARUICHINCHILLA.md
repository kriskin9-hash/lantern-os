# Cloud-First User Migration: Gage, Courtney, Waruichinchilla

Generated: 2026-05-28
Status: Implementation in progress

## Purpose

Enable cloud-first access to Lantern OS chat and RAG models for gage, courtney, and waruichinchilla via Codex Cloud environment.

## Target Users

| User | Access Type | RAG Context | Setup Priority |
|---|---|---|---|
| gage | Codex Cloud + Discord | School art packet, family context, learning focus | P0 |
| courtney | Codex Cloud + Discord | Family context, collaboration focus | P0 |
| waruichinchilla | Codex Cloud + Discord | External collaborator, project focus | P1 |

## Architecture

```text
Codex Cloud Environment
├── GitHub Connector: alex-place/lantern-os (private)
├── User-Specific RAG Context
├── Chat Interfaces
│   ├── Discord Lounge Bot (multi-channel support)
│   └── Lantern Garage Web App (user-aware sessions)
└── RAG Model Updates
    ├── User profile entries in external cache
    ├── Personalized retrieval context
    └── Internal house RAG updates
```

## Implementation Steps

### Phase 1: RAG Context Creation
- [ ] Create user-specific RAG cache entries
- [ ] Add user context to internal house RAG
- [ ] Update RAG dollhouse with user profiles

### Phase 2: Cloud Access Setup
- [ ] Configure Codex Cloud environment
- [ ] Set up GitHub connector for private repo access
- [ ] Create user-specific environment instructions

### Phase 3: Chat Infrastructure Enhancement
- [ ] Extend Discord bot for multi-channel support
- [ ] Add user awareness to Lantern Garage app
- [ ] Create user session management

### Phase 4: Documentation and Training
- [ ] Create user setup guides
- [ ] Document chat interface usage
- [ ] Provide RAG context understanding

## User-Specific RAG Context

### Gage
- **Context**: School art packet recipient, family member, learning focus
- **RAG Topics**: Art education, school projects, family learning activities
- **Access Level**: Family-safe content, educational materials

### Courtney  
- **Context**: Family member, collaboration partner
- **RAG Topics**: Family projects, collaboration workflows, shared decision making
- **Access Level**: Family collaboration content, project management

### Waruichinchilla
- **Context**: External collaborator, project partner
- **RAG Topics**: Project-specific context, technical collaboration
- **Access Level**: Project-related content, technical documentation

## Safety Boundaries

- No private credentials or personal data in RAG cache
- Age-appropriate content filtering for gage
- Family-safe boundaries for all users
- Project-scoped access for external collaborators
- No operator secrets or sensitive configurations

## Next Actions

1. Create user-specific RAG cache entries using Add-ExternalRagCacheItem.ps1
2. Update internal house RAG with user context
3. Create Codex Cloud setup documentation
4. Test multi-user chat access