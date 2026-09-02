from fastapi import FastAPI , HTTPException
from app.models import DockerfileAnalysis, DockerfileRequest
from google import genai
from google.genai import types

client = genai.Client(
    vertexai=True,
    project="dev-8fenak",
    location="global"
)
model =  "gemini-2.5-flash-lite"

app = FastAPI(
    title="AI Dockerfile Optimizer",
    version="0.1.0",
)

@app.get("/health")
def health():
    return{"status": "Ok"}

@app.post("/optimize")
def optimize(request: DockerfileRequest, response_model=DockerfileAnalysis):
    prompt = f"""
You are a senior DevOps engineer reviewing a Dockerfile.

Analyze this Dockerfile and provide a concise optimization report.

Rules:
- Return at most 5 findings.
- Prioritize the most important issues.
- Each finding must have a one-sentence issue.
- Each recommendation must be one sentence.
- Do not provide explanations outside the required JSON.
- Do not invent problems that cannot be inferred from the Dockerfile.
- Only recommend changes that are appropriate for the given Dockerfile.

Focus on:
1. Security
2. Image size
3. Build/cache efficiency
4. Reliability
5. Docker best practices

Then provide an optimized Dockerfile.

Dockerfile:
```dockerfile
{request.dockerfile}
"""
    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=DockerfileAnalysis,
            )
        )
        if not response.text:
            raise HTTPException(
                status_code=500,
                detail="Gemini returned an empty response",
            )
        return DockerfileAnalysis.model_validate_json(response.text)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Gemini request failed. {e}"
        )
    