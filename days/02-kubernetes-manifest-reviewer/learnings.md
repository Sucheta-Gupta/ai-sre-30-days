# Day 2 — AI Kubernetes Manifest Reviewer

## What I Built

Built a FastAPI-based Kubernetes manifest reviewer that combines deterministic validation with AI-powered semantic analysis.

### Architecture

```text
Kubernetes YAML
      ↓
YAML parsing
      ↓
Deterministic validation
      ↓
Gemini semantic analysis
      ↓
Structured JSON response
      ↓
Pydantic validation
```

The API accepts a Kubernetes manifest and returns:

- A summary
- A score from 0–100
- Structured findings
- Severity
- Category
- Issue
- Recommendation

---

## Key Learning 1 — Deterministic Validation vs AI Analysis

One of the most important lessons from Day 2 was understanding that not every problem should be delegated to an LLM.

I implemented deterministic validation for basic Kubernetes structure and known rules, such as:

- Missing `kind`
- Unsupported resource types
- Missing `metadata`
- Missing `metadata.name`
- Missing `spec`
- Missing `replicas`
- Missing Pod template
- Missing containers
- Missing container name
- Missing container image

These checks are predictable and should be handled by normal code.

Gemini is then responsible for higher-level semantic analysis such as:

- Security recommendations
- Missing probes
- Resource configuration
- Reliability concerns
- Kubernetes best practices

The resulting principle is:

> **Use deterministic code for facts and validation; use AI for interpretation and recommendations.**

---

## Key Learning 2 — Pydantic Models Create a Contract

I used Pydantic models to define both the API request and the expected AI response.

The AI response has a strict structure:

```text
K8sManifestAnalysis
├── summary
├── score
└── findings[]
       ├── severity
       ├── category
       ├── issue
       └── recommendation
```

I also restricted fields such as `severity` and `category` using `Literal`.

This means the application isn't simply trusting arbitrary text returned by Gemini.

The model has to conform to a defined schema.

---

## Key Learning 3 — A Pydantic Class Is Not an Instance

I learned the difference between:

```python
ValidationFindings
```

and:

```python
ValidationFindings(issues=[])
```

The first is the model definition.

The second creates an actual instance that contains data.

Therefore, to add findings I work with the instance:

```python
findings.issues.append(...)
```

This distinction became important when building the deterministic validator.

---

## Key Learning 4 — Working With Nested Kubernetes YAML

Kubernetes manifests are deeply nested dictionaries and lists.

I learned to navigate them safely using:

```python
dictionary.get("key")
```

and:

```python
"key" in dictionary
```

For example:

```text
manifest
  └── spec
       └── template
            └── spec
                 └── containers[]
```

I also learned that `containers` is a list of dictionaries, so it needs to be iterated differently from a dictionary.

For example, conceptually:

```text
containers
    ↓
list
    ↓
container
    ↓
dictionary
```

This helped me understand how Kubernetes YAML maps into Python data structures after `yaml.safe_load()`.

---

## Key Learning 5 — Guard Clauses Make Validation Easier to Read

Initially, nested validation can quickly become a large collection of `if/else` blocks.

I learned that guard clauses can keep the validation logic flatter.

For example, if the resource isn't a Deployment, there is no reason to continue running Deployment-specific validation.

This makes the control flow easier to understand without necessarily splitting every tiny check into another function.

---

## Key Learning 6 — LLM Output Can Be Plausible but Wrong

This was one of the most valuable lessons.

Gemini produced useful recommendations, but it also produced questionable ones.

Examples included:

- Recommending a `PodDisruptionBudget` without knowing whether the workload actually requires one.
- Recommending an explicit termination grace period even though Kubernetes already has a default.
- Suggesting `runAsUser`, which can be inappropriate if the correct UID isn't known.
- Treating some best-practice recommendations as actual problems.

This demonstrated an important principle:

> **An LLM can produce technically plausible recommendations that aren't necessarily appropriate.**

AI output therefore needs validation and careful evaluation.

---

## Key Learning 7 — Prompting Is Not a Substitute for Program Logic

I attempted to tell Gemini not to duplicate deterministic findings.

The model still independently identified the missing container image.

This showed that asking an LLM to enforce a deterministic rule isn't always reliable.

A better production architecture could eventually be:

```text
Deterministic findings
        +
AI findings
        ↓
Deterministic deduplication
        ↓
Final findings
```

In other words:

> **Don't rely on an LLM to enforce rules that code can enforce reliably.**

The LLM can be instructed not to duplicate findings, but the application should ultimately enforce this rule if it matters.

---

## Key Learning 8 — AI Applications Need Evaluation

The `/review` endpoint successfully returned valid JSON, but that alone doesn't mean the application is good.

I tested the output by asking:

- Did deterministic validation catch the obvious problem?
- Did Gemini find additional issues?
- Did Gemini duplicate an existing finding?
- Are the recommendations actually useful?
- Are the severity levels reasonable?
- Is the model inventing unnecessary recommendations?
- Is the AI reviewing the entire manifest?

This changed my thinking from:

> "The LLM returned a response, so it works."

to:

> **"The system returned a response; now I need to evaluate whether that response is correct and useful."**

---

## Key Learning 9 — Structured AI Output

Instead of asking Gemini to return free-form text, I used a structured response schema.

The expected output contains:

```text
summary
score
findings[]
```

Each finding contains:

```text
severity
category
issue
recommendation
```

This makes the AI response much easier for an application to consume.

It also allows Pydantic to validate the response before returning it to the API client.

This is an important pattern for production AI systems:

> **LLM → structured output → application validation → user**

rather than:

> **LLM → arbitrary text → user**

---

## Key Learning 10 — Exception Handling Around AI Calls

I also implemented different handling for different failure types.

### Invalid YAML

Returns:

```text
HTTP 400
```

because the user's input is invalid.

### Empty Gemini response

Returns:

```text
HTTP 500
```

because the application expected an AI response but didn't receive one.

### Gemini/API failure

Returns:

```text
HTTP 500
```

because the failure is on the application/service side.

I also learned why:

```python
except HTTPException:
    raise
```

is important.

It prevents an intentionally raised HTTP error from being accidentally caught and converted into another generic `500` error.

---

## Key Learning 11 — The LLM Is a Component, Not the Application

Day 1 introduced the idea that an LLM is a component.

Day 2 reinforced it.

The application is not:

```text
Kubernetes YAML → Gemini
```

It is:

```text
Kubernetes YAML
       ↓
Application logic
       ↓
Deterministic validation
       ↓
LLM reasoning
       ↓
Structured output
       ↓
Application validation
       ↓
API response
```

The LLM is only one part of the overall system.

The surrounding software determines how reliable and useful the AI feature actually is.

---

## Final Architecture

```text
                  Kubernetes YAML
                         │
                         ▼
                  FastAPI /review
                         │
                         ▼
                   YAML parsing
                         │
                         ▼
              Deterministic validation
                         │
                         │ findings
                         ▼
                  Gemini 2.5 Flash
                         │
                         ▼
                 Structured response
                         │
                         ▼
                    Pydantic
                         │
                         ▼
                    API response
```

---

## What I Would Improve Later

I intentionally stopped Day 2 without over-engineering it.

Future improvements could include:

1. Deterministic deduplication of AI findings
2. Better validation of AI recommendations
3. More Kubernetes resource types
4. Better severity scoring
5. Unit tests for deterministic validation
6. Integration tests for the `/review` endpoint
7. Evaluation against a collection of known-good and intentionally bad manifests
8. Kubernetes schema validation
9. More sophisticated semantic validation
10. A better mechanism for distinguishing actual problems from optional best practices

---

## Day 2 Takeaway

The biggest lesson from this project:

> **Building an AI feature isn't just connecting an LLM to an API. The real engineering work is defining what the LLM should do, what it should NOT do, validating its output, and deciding which parts must remain deterministic.**

A production AI system should combine:

```text
Deterministic logic
        +
LLM reasoning
        +
Structured contracts
        +
Validation
        +
Evaluation
```

rather than relying on the LLM alone.

---

## Day 2 Status

**Complete ✅**

Built an AI-powered Kubernetes manifest reviewer using:

- Python
- FastAPI
- Pydantic
- Google Gemini / Vertex AI
- YAML parsing
- Deterministic validation
- Structured LLM output

The project successfully accepts a Kubernetes manifest and produces an AI-assisted review with structured findings.