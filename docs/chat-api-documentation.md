# Chat API Documentation

## Overview
The Chat API provides comprehensive functionality for managing chat sessions and messages within the GenAI-powered software testing assistance platform. All endpoints require JWT authentication and follow RESTful conventions.

## Base URL
```
/api/v1/chat
```

## Authentication
All endpoints require JWT authentication via the `Authorization` header:
```
Authorization: Bearer <jwt_token>
```

## Data Models

### ChatSession
```json
{
  "id": "uuid",
  "title": "string",                      // Default: "New Chat"
  "user_id": "uuid",
  "project_id": "uuid",                   // Required - every session must belong to a project
  "system_prompt": "string",
  "history_strategy": "string",           // Default: "all"
  "memory_type": "string",                // Default: "default" 
  "context_window": "integer",            // Default: 10
  "current_message_sequence_num": "integer", // Default: 0
  "agent_state": "object",                // Default: {}
  "graph_id": "string",
  "meta_data": "object",                  // Default: {}
  "memory_config": "object",              // Default: {}
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### ChatMessage
```json
{
  "sequence_num": "integer",
  "chat_id": "uuid",
  "content": "string",
  "message_type": "string",       // "human" | "ai" | "system"
  "parent_id": "integer",
  "is_streaming": "boolean",
  "stream_complete": "boolean",
  "status": "string",             // "pending" | "streaming" | "complete" | "error"
  "chunk_sequence": "integer",
  "meta_data": "object",
  "additional_kwargs": "object",
  "function_name": "string",
  "function_args": "object",
  "function_output": "object",
  "node_id": "string",
  "step_id": "string",
  "status_details": "string",
  "importance_score": "float",
  "embedding_id": "string",
  "created_at": "datetime"
}
```

## Endpoints

### Chat Sessions

#### Create Chat Session
```http
POST /sessions
```

**Request Body:**
```json
{
  "title": "string",                       // Optional, default="New Chat"
  "project_id": "uuid",                    // Required
  "system_prompt": "string",               // Optional
  "history_strategy": "string",            // Optional, default="all"
  "memory_type": "string",                 // Optional, default="default"
  "context_window": "integer",             // Optional, default=10
  "current_message_sequence_num": "integer", // Optional, default=0
  "agent_state": "object",                 // Optional
  "graph_id": "string",                    // Optional
  "meta_data": "object",                   // Optional
  "memory_config": "object"                // Optional
}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "title": "string",
  "user_id": "uuid",
  "project_id": "uuid",
  "system_prompt": "string",
  "history_strategy": "string",
  "memory_type": "string",
  "context_window": "integer",
  "current_message_sequence_num": "integer",
  "agent_state": "object",
  "graph_id": "string",
  "meta_data": "object",
  "memory_config": "object",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

**Description:** Creates a new chat session associated with a project. The user_id is automatically set from the authenticated user.

---

#### List Chat Sessions
```http
GET /sessions?project_id={uuid}&page={int}&size={int}
```

**Query Parameters:**
- `project_id` (optional): Filter sessions by project ID
- `page` (optional, default=1): Page number (1-based)
- `size` (optional, default=20, max=100): Number of sessions per page

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "string",
      // ... ChatSession fields
    }
  ],
  "total": "integer",
  "page": "integer",
  "size": "integer",
  "pages": "integer"
}
```

**Description:** Retrieves paginated list of chat sessions for the authenticated user, optionally filtered by project.

---

#### Get Specific Chat Session
```http
GET /sessions/{session_id}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "title": "string",
  // ... ChatSession fields
}
```

**Error Responses:**
- `404 Not Found`: Session not found
- `403 Forbidden`: User doesn't own this session

**Description:** Retrieves details of a specific chat session.

---

#### Update Chat Session
```http
PUT /sessions/{session_id}
```

**Request Body:**
```json
{
  "title": "string",                       // Optional
  "system_prompt": "string",               // Optional
  "history_strategy": "string",            // Optional
  "memory_type": "string",                 // Optional
  "context_window": "integer",             // Optional
  "agent_state": "object",                 // Optional
  "meta_data": "object"                    // Optional
  // ... other updatable fields
}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "title": "string",
  // ... updated ChatSession fields
}
```

**Error Responses:**
- `404 Not Found`: Session not found
- `403 Forbidden`: User doesn't own this session

**Description:** Updates an existing chat session. Only provided fields are updated.

---

#### Delete Chat Session
```http
DELETE /sessions/{session_id}
```

**Response:** `200 OK`
```json
{
  "message": "Chat session deleted successfully"
}
```

**Error Responses:**
- `404 Not Found`: Session not found
- `403 Forbidden`: User doesn't own this session

**Description:** Permanently deletes a chat session and all associated messages.

---

### Chat Messages

#### Get Session with Messages
```http
GET /sessions/{session_id}/messages?limit={int}
```

**Query Parameters:**
- `limit` (optional, default=50, max=200): Number of recent messages to include

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "title": "string",
  "user_id": "uuid",
  "project_id": "uuid",
  "system_prompt": "string",
  "history_strategy": "string",
  "memory_type": "string",
  "context_window": "integer",
  "current_message_sequence_num": "integer",
  "agent_state": "object",
  "graph_id": "string",
  "meta_data": "object",
  "memory_config": "object",
  "created_at": "datetime",
  "updated_at": "datetime",
  "messages": [
    {
      "sequence_num": "integer",
      "content": "string",
      "message_type": "string",
      "status": "string",
      // ... other ChatMessage fields
    }
  ]
}
```

**Error Responses:**
- `404 Not Found`: Session not found
- `403 Forbidden`: User doesn't own this session

**Description:** Retrieves a chat session along with its recent messages. Messages are ordered by sequence number (most recent first) and limited by the `limit` parameter.

---

#### Update Chat Message
```http
PUT /sessions/{session_id}/messages/{sequence_num}
```

**Request Body:**
```json
{
  "content": "string"                      // Required - updated content for the message
}
```

**Response:** `200 OK`
```json
{
  "sequence_num": "integer",
  "chat_id": "uuid", 
  "content": "string",
  "message_type": "string",
  "status": "string",
  "parent_id": "integer",
  "is_streaming": "boolean",
  "stream_complete": "boolean",
  "chunk_sequence": "integer",
  "meta_data": "object",
  "additional_kwargs": "object",
  "function_name": "string",
  "function_args": "object",
  "function_output": "object",
  "node_id": "string",
  "step_id": "string",
  "status_details": "string",
  "importance_score": "float",
  "embedding_id": "string",
  "created_at": "datetime"
}
```

**Error Responses:**
- `404 Not Found`: Session or message not found
- `403 Forbidden`: User doesn't own this session

**Description:** Updates the content of a specific chat message identified by its sequence number within a session.

---

#### Delete Chat Message
```http
DELETE /sessions/{session_id}/messages/{sequence_num}
```

**Response:** `200 OK`
```json
{
  "message": "Chat message deleted successfully"
}
```

**Error Responses:**
- `404 Not Found`: Session or message not found
- `403 Forbidden`: User doesn't own this session

**Description:** Permanently deletes a specific chat message. This also updates the session's `updated_at` timestamp.

---

#### Send Message with Streaming Response
```http
POST /sessions/{session_id}/messages/stream
```

**Request Body:**
```json
{
  "content": "string",                     // Required - message content
  "message_type": "string",                // Optional, default="human" - "human" | "ai" | "system"
  "parent_id": "integer",                  // Optional - parent message sequence number for threading
  "meta_data": "object",                   // Optional - additional metadata
  "stream": "boolean"                      // Optional, default=true for streaming endpoint
}
```

**Response:** `200 OK` (Server-Sent Events)
```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive

data: {"type": "message_start", "sequence_num": 1, "chunk_sequence": 0, "message_id": "session_id:1", "metadata": {"status": "started"}}

data: {"type": "content_chunk", "sequence_num": 1, "chunk_sequence": 1, "delta": "Hello", "content": "Hello", "message_id": "session_id:1"}

data: {"type": "content_chunk", "sequence_num": 1, "chunk_sequence": 2, "delta": " there!", "content": "Hello there!", "message_id": "session_id:1"}

data: {"type": "message_end", "sequence_num": 1, "chunk_sequence": 3, "content": "Hello there!", "message_id": "session_id:1", "metadata": {"status": "completed", "total_chunks": 2}}
```

**Error Response:**
```
data: {"type": "error", "sequence_num": 1, "chunk_sequence": 1, "error": "Error message", "message_id": "session_id:1"}
```

**Error Responses:**
- `404 Not Found`: Session not found
- `403 Forbidden`: User doesn't own this session

**Description:** Sends a message to the chat session and receives a real-time streaming response from the AI agent. The response is delivered as Server-Sent Events (SSE) with different event types for message lifecycle management. The AI agent uses the conversation history (limited by `context_window`) and project context to generate contextually relevant responses.

## Streaming Event Types

### message_start
Indicates the beginning of AI response generation.
```json
{
  "type": "message_start",
  "sequence_num": "integer",
  "chunk_sequence": 0,
  "message_id": "string",
  "metadata": {
    "status": "started"
  }
}
```

### content_chunk
Contains incremental content from the AI response.
```json
{
  "type": "content_chunk",
  "sequence_num": "integer",
  "chunk_sequence": "integer",
  "delta": "string",                       // New content in this chunk
  "content": "string",                     // Full content so far
  "message_id": "string"
}
```

### message_end
Indicates completion of AI response generation.
```json
{
  "type": "message_end",
  "sequence_num": "integer",
  "chunk_sequence": "integer",
  "content": "string",                     // Final complete content
  "message_id": "string",
  "metadata": {
    "status": "completed",
    "total_chunks": "integer"
  }
}
```

### error
Indicates an error occurred during response generation.
```json
{
  "type": "error",
  "sequence_num": "integer",
  "chunk_sequence": "integer",
  "error": "string",                       // Error description
  "message_id": "string"
}
```

## Error Handling

### Standard HTTP Status Codes
- `200 OK`: Request successful
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Access denied (user doesn't own resource)
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation errors
- `500 Internal Server Error`: Server error

### Error Response Format
```json
{
  "detail": "Error description"
}
```

## Usage Examples

### Creating a Chat Session
```javascript
const response = await fetch('/api/v1/chat/sessions', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    title: 'Test Planning Session',
    project_id: 'project-uuid-here',
    system_prompt: 'You are a helpful QA testing assistant.',
    context_window: 20,  // Use 20 previous messages for context
    history_strategy: 'all',
    memory_type: 'default'
  })
});
const session = await response.json();
```

### Streaming Chat
```javascript
const response = await fetch(`/api/v1/chat/sessions/${sessionId}/messages/stream`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    content: 'Help me create test cases for login functionality',
    message_type: 'human',
    stream: true  // Explicitly enable streaming
  })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { value, done } = await reader.read();
  if (done) break;
  
  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');
  
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      try {
        const data = JSON.parse(line.slice(6));
        
        switch (data.type) {
          case 'message_start':
            console.log('AI started responding...');
            console.log('Message ID:', data.message_id);
            break;
          case 'content_chunk':
            console.log('New content delta:', data.delta);
            console.log('Full content so far:', data.content);
            console.log('Chunk sequence:', data.chunk_sequence);
            break;
          case 'message_end':
            console.log('AI finished responding');
            console.log('Final content:', data.content);
            console.log('Total chunks:', data.metadata?.total_chunks);
            break;
          case 'error':
            console.error('Error:', data.error);
            console.error('At sequence:', data.sequence_num);
            break;
        }
      } catch (parseError) {
        console.error('Failed to parse SSE data:', parseError);
      }
    }
  }
}
```

### Getting Recent Messages
```javascript
const response = await fetch(`/api/v1/chat/sessions/${sessionId}/messages?limit=20`, {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
const sessionWithMessages = await response.json();
```

## Rate Limits
- **Message sending**: 60 requests per minute per user
- **Session operations**: 100 requests per minute per user
- **Message retrieval**: 200 requests per minute per user

## Notes
- All timestamps are in ISO 8601 format (UTC)
- UUIDs are in standard UUID v4 format
- Streaming responses use Server-Sent Events (SSE) protocol
- Message sequence numbers are auto-incrementing integers within each session (not UUIDs)
- Project association is required for all chat sessions (enforced at database level)
- Messages are identified by their sequence number within a session, not by UUID
- The `context_window` parameter controls how many previous messages are used for AI context (default: 10)
- Chat sessions support various configuration options through `agent_state`, `meta_data`, and `memory_config` fields

---

**API Version**: v1  
**Last Updated**: July 23, 2025  
**Authentication**: JWT Bearer Token Required
