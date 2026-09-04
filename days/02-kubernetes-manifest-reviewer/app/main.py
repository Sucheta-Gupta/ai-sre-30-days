from __future__ import annotations
from app.models import K8sManifestRequest, K8sManifestAnalysis , ValidationFindings
from fastapi import FastAPI, HTTPException
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
import yaml
from pprint import pprint


load_dotenv()
project =  os.getenv('project') if os.getenv('project') else "dev-project"
model = os.getenv('model') if os.getenv("model") else "gemini-2.5-flash-lite"

app = FastAPI(
    title="K8S Manifest Analyser",
    version="0.1.0"
)

client = genai.Client(
    vertexai=True,
    project=project,
    location="global"
)


def validate_yaml_refactored(manifest: dict):
    findings = ValidationFindings(issues =[])
    if not manifest.get("kind"):
        findings.issues.append("missing kind")
        return findings
    if manifest.get("kind").lower() != "deployment":
        findings.issues.append(f"Rules undefined for the resource {manifest.get('kind')}")
        return findings
    if not manifest.get("metadata"):
        findings.issues.append("missing metadata")
    else:
        metadata = manifest.get("metadata")
        if not metadata.get("name"):
            findings.issues.append("missing metadata.name")
    if not manifest.get("spec"):
        findings.issues.append("missing spec")
    else:
        spec = manifest.get("spec")
        if "replicas"  not in spec:
            findings.issues.append("missing replicas")
        if spec.get("replicas") == 0:
            findings.issues.append("replica count set to  0")
        if spec.get("template") is None:
            findings.issues.append("missing spec.template")
        else:
            template = spec.get("template")
            if template.get("spec") is None:
                findings.issues.append("missing spec.template.spec")
            else:
                template_spec = template.get("spec")
                if not template_spec.get("containers"):
                    findings.issues.append("missing spec.template.spec.containers")
                else: 
                    containers = template_spec.get("containers")
                    for container in containers:
                        if not container.get("name"):
                            findings.issues.append(f"missing spec.template.spec.containers.name ")  
                        if not container.get("image"):
                            findings.issues.append(f"missing Container image for container {container.get('name')}")                     
    return findings

@app.get("/health")
def health():
    return {"status" : "Ok"}

@app.post("/review",response_model=K8sManifestAnalysis)
def review(request: K8sManifestRequest):

    try:
        raw_data = yaml.safe_load(request.manifest)
        findings = validate_yaml_refactored(raw_data)
    except yaml.YAMLError:
        raise HTTPException(
                status_code = 400,
                detail="Invalid Yaml"

        )
    prompt = f"""
    You are a senior DevOps engineer reviewing a Kubernetes Manifest.

    Analyze this Manifest and deterministic findings and provide a concise optimization report.

    The manifest is preparsed for deterministic failures and the findings are available 
    Independently perform a complete semantic review and identify additional issues, while avoiding duplication of deterministic findings.

    Rules:
    - Return at most 10 findings.
    - Prioritize the most important issues.
    - Each finding must have a one-sentence issue.
    - Each recommendation must be one sentence.
    - Do not provide explanations outside the required JSON.
    - Do not invent problems that cannot be inferred from the Manifest.
    - Only recommend changes that are appropriate for the given Manifest.
    - Only Categorise the manifest based on the categories and return Others if no match is found
    - If the findings are present , do not analyse them or report them

    Focus on:
    1. Security
    2. Network and Routing
    3. Observability
    4. Reliability
    5. Kubernetes best practices
    6. Configuration
    7. Missing Probes

    Then provide analysis.

    Manifest:
    ```Manifest
    {request.manifest}

    Findings
    {findings}
    ```
    """
    try:
        pprint(prompt)
        response = client.models.generate_content(
            contents = prompt,
            model = model,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=K8sManifestAnalysis,
            )
        )
        if not response.text:
            raise HTTPException(
                    status_code = 500,
                    detail="Gemini returned an empty response"

            )
            
        return K8sManifestAnalysis.model_validate_json(response.text)
    except HTTPException as e:
        raise 
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Gemini request failed. {e}"
        )
    

