# Azure Responses API SDK - Architecture Diagrams

## 🏗️ SDK Class Hierarchy

```mermaid
classDiagram
    class AIProjectClient {
        +endpoint: str
        +credential: TokenCredential
        +get_openai_client() OpenAI
        +close()
        +send_request()
    }
    
    class OpenAI {
        +base_url: str
        +responses: Responses
        +chat: Chat
        +embeddings: Embeddings
        +files: Files
        +vector_stores: VectorStores
        +images: Images
    }
    
    class Responses {
        +create() Response
        +retrieve() Response
        +delete() DeletedResponse
        +cancel() Response
        +stream() Stream
        +parse() ParsedResponse
        +compact() CompactedResponse
        +input_items: InputItems
    }
    
    class InputItems {
        +list() ResponseItemList
    }
    
    class Response {
        +id: str
        +status: str
        +model: str
        +output: List~OutputItem~
        +output_text: str
        +usage: ResponseUsage
        +previous_response_id: str
        +created_at: float
        +completed_at: float
    }
    
    class ResponseUsage {
        +input_tokens: int
        +output_tokens: int
        +total_tokens: int
    }
    
    AIProjectClient --> OpenAI : get_openai_client()
    OpenAI --> Responses : responses
    Responses --> InputItems : input_items
    Responses --> Response : returns
    Response --> ResponseUsage : usage
```

## 🔄 Request Flow

```mermaid
flowchart TB
    subgraph Client["Client Setup"]
        A[AIProjectClient] -->|get_openai_client| B[OpenAI Client]
        B -->|auto-configured| C[base_url + auth]
    end
    
    subgraph Request["Request Phase"]
        D[responses.create] -->|input| E{Input Type}
        E -->|simple| F[String]
        E -->|structured| G[Message List]
        E -->|multimodal| H[Text + Image/PDF]
    end
    
    subgraph Processing["Azure Processing"]
        I[Azure Foundry] -->|model inference| J[GPT Model]
        J -->|tool calls?| K{Tools}
        K -->|yes| L[Execute Tools]
        L --> J
        K -->|no| M[Generate Output]
    end
    
    subgraph Response["Response Phase"]
        M --> N[Response Object]
        N --> O[output_text]
        N --> P[usage]
        N --> Q[id for chaining]
    end
    
    C --> D
    H --> I
    G --> I
    F --> I
```

## 🔧 Tool Types

```mermaid
flowchart LR
    subgraph Tools["Available Tools"]
        T1[function]
        T2[file_search]
        T3[code_interpreter]
        T4[web_search]
        T5[mcp]
        T6[computer_use]
        T7[image_generation]
    end
    
    subgraph FunctionTool["Function Tool"]
        T1 --> F1[name]
        T1 --> F2[description]
        T1 --> F3[parameters]
        F3 --> F4[JSON Schema]
    end
    
    subgraph FileSearchTool["File Search Tool"]
        T2 --> FS1[vector_store_ids]
        T2 --> FS2[max_num_results]
    end
    
    subgraph CodeInterpreter["Code Interpreter"]
        T3 --> CI1[container]
        CI1 --> CI2[type: auto]
        CI1 --> CI3[file_ids]
    end
    
    subgraph MCPTool["MCP Tool"]
        T5 --> M1[server_url]
        T5 --> M2[server_label]
        T5 --> M3[require_approval]
        T5 --> M4[headers]
    end
```

## 🔗 Response Chaining (Multi-Turn)

```mermaid
sequenceDiagram
    participant U as User
    participant C as Client
    participant A as Azure Foundry
    participant S as State Store
    
    U->>C: responses.create(input="Hello")
    C->>A: POST /responses
    A->>S: Store conversation
    A-->>C: Response (id: resp_001)
    C-->>U: response.output_text
    
    Note over U,S: Turn 2 - Chained
    
    U->>C: responses.create(previous_response_id="resp_001", input="Tell me more")
    C->>A: POST /responses
    A->>S: Retrieve resp_001 context
    S-->>A: Previous conversation
    A->>A: Generate with full context
    A->>S: Store updated conversation
    A-->>C: Response (id: resp_002)
    C-->>U: response.output_text
    
    Note over U,S: Delete after 30 days or manually
    
    U->>C: responses.delete("resp_001")
    C->>A: DELETE /responses/resp_001
    A->>S: Remove from store
```

## 📥 Input Structure

```mermaid
flowchart TD
    subgraph InputTypes["Input Parameter"]
        I[input]
        I --> S[String]
        I --> M[Message List]
    end
    
    subgraph Message["Message Structure"]
        M --> R[role: user/assistant/system]
        M --> C[content]
    end
    
    subgraph Content["Content Types"]
        C --> T[input_text]
        C --> IMG[input_image]
        C --> F[input_file]
    end
    
    subgraph TextContent["Text Content"]
        T --> T1["type: input_text"]
        T --> T2["text: string"]
    end
    
    subgraph ImageContent["Image Content"]
        IMG --> I1["type: input_image"]
        IMG --> I2["image_url: URL or base64"]
    end
    
    subgraph FileContent["File Content"]
        F --> F1["type: input_file"]
        F --> F2["file_id: string"]
        F --> F3["file_data: base64"]
        F --> F4["filename: string"]
    end
```

## 📤 Output Structure

```mermaid
flowchart TD
    subgraph ResponseOutput["response.output"]
        O[output: List]
    end
    
    subgraph OutputTypes["Output Item Types"]
        O --> MSG[message]
        O --> FC[function_call]
        O --> CI[code_interpreter_call]
        O --> FS[file_search_call]
        O --> WS[web_search_call]
        O --> IG[image_generation_call]
    end
    
    subgraph MessageOutput["Message Output"]
        MSG --> MSG1[role: assistant]
        MSG --> MSG2[content]
        MSG2 --> MSG3[text]
        MSG2 --> MSG4[refusal]
    end
    
    subgraph FunctionCall["Function Call Output"]
        FC --> FC1[name]
        FC --> FC2[call_id]
        FC --> FC3[arguments: JSON]
    end
    
    subgraph CodeInterpreterOutput["Code Interpreter Output"]
        CI --> CI1[code]
        CI --> CI2[outputs]
        CI2 --> CI3[logs]
        CI2 --> CI4[files]
    end
```

## 🌊 Streaming Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant A as Azure
    
    C->>A: responses.create(stream=True)
    
    A-->>C: response.created
    A-->>C: response.in_progress
    
    loop Text Generation
        A-->>C: response.output_text.delta
        Note right of C: Print chunk
    end
    
    A-->>C: response.output_text.done
    A-->>C: response.completed
    
    Note over C,A: Final response object available
```

## ⏳ Background Task Flow

```mermaid
stateDiagram-v2
    [*] --> Queued: background=True
    Queued --> InProgress: Processing starts
    InProgress --> Completed: Success
    InProgress --> Failed: Error
    InProgress --> Cancelled: User cancels
    
    Completed --> [*]
    Failed --> [*]
    Cancelled --> [*]
    
    note right of Queued: Immediate return
    note right of InProgress: Poll with retrieve()
    note right of Cancelled: cancel() called
```

## 🔐 Authentication Flow

```mermaid
flowchart LR
    subgraph Azure["Azure Identity"]
        DC[DefaultAzureCredential]
        DC --> E[Environment Variables]
        DC --> M[Managed Identity]
        DC --> CLI[Azure CLI]
        DC --> VS[VS Code]
    end
    
    subgraph Client["Client Setup"]
        DC --> AIP[AIProjectClient]
        AIP --> |inject token| OAI[OpenAI Client]
        OAI --> |Authorization header| REQ[API Request]
    end
    
    subgraph Azure Foundry["Azure Foundry"]
        REQ --> VAL[Validate Token]
        VAL --> |scope: cognitiveservices| API[Responses API]
    end
```

## 📊 Complete Data Flow

```mermaid
flowchart TB
    subgraph Setup["1. Setup"]
        A1[Load .env] --> A2[Create AIProjectClient]
        A2 --> A3[Get OpenAI Client]
    end
    
    subgraph Request["2. Create Request"]
        B1[Define model]
        B2[Prepare input]
        B3[Configure tools]
        B4[Set parameters]
        B1 & B2 & B3 & B4 --> B5[responses.create]
    end
    
    subgraph Process["3. Azure Processing"]
        C1[Authenticate]
        C2[Route to Model]
        C3{Need Tools?}
        C4[Execute Tools]
        C5[Generate Response]
        C1 --> C2 --> C3
        C3 -->|Yes| C4 --> C2
        C3 -->|No| C5
    end
    
    subgraph Response["4. Handle Response"]
        D1[Check status]
        D2[Extract output_text]
        D3[Get usage stats]
        D4[Save response.id]
    end
    
    subgraph Chain["5. Multi-Turn"]
        E1[New input]
        E2[Pass previous_response_id]
        E3[Continue conversation]
    end
    
    A3 --> B5
    B5 --> C1
    C5 --> D1
    D4 --> E2
    E2 --> B5
```
