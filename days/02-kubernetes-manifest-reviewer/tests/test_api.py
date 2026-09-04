from app.main import health , app
from fastapi.testclient import TestClient
from fastapi.testclient import TestClient
from unittest.mock import patch , Mock
import pytest
import yaml


@pytest.fixture
def valid_manifest() ->dict:
    return {
"apiVersion": "apps/v1",
    "kind": "Deployment",
    "metadata": {
        "name": "demo-app",
        "labels": {
            "app": "demo-app"
        }
    },
    "spec": {
        "replicas": 2,
        "selector": {
            "matchLabels": {
                "app": "demo-app"
            }
        },
        "template": {
            "metadata": {
                "labels": {
                    "app": "demo-app"
                }
            },
            "spec": {
                "containers": [
                    {
                        "name": "demo-app",
                        "image": "nginx:1.27",
                        "ports": [
                            {
                                "containerPort": 80
                            }
                        ]
                    }
                ]
            }
        }
    }

    }





def test_health():
    response = health()
    assert response == {"status" : "Ok"}



def test_review_invalid_yaml():
    invalid_yaml = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: demo-app
spec:
  replicas: 2
  template:
    spec:
      containers:
        - name: demo-app
          image: nginx:1.27
          ports: [80
"""

    client = TestClient(app)
    response = client.post("/review",    
                json={
        "manifest": invalid_yaml
    })
    assert response.status_code == 400

@patch("app.main.client.models.generate_content")
def test_review_valid_yaml(mock_generate_content,valid_manifest):
    fake_response = Mock()
    fake_response.text = '{"summary": "The deployment looks good.", "score": 90, "findings": []}'
    mock_generate_content.return_value = fake_response   
    
    client = TestClient(app)
    response = client.post("/review",    
                json={
        "manifest": yaml.dump(valid_manifest)
    })

    """
    Fastapi response model is K8sManifestAnalysis
    and doing this return K8sManifestAnalysis.model_validate_json(response.text)
    pydantic serialises that Pydantic object back into an HTTP JSON response.
    So response.text is a JSON string, and comparing the raw string is brittle because JSON formatting can differ.
    using response.json() That converts the HTTP response JSON into a Python dictionary.
    It should be equivalent to:
    {
    "summary": "The deployment looks good.",
    "score": 90,
    "findings": []
    }
    """
    assert response.status_code == 200
    assert response.json()["summary"] == "The deployment looks good."
    assert response.json()["score"] == 90
    assert response.json()["findings"] == []


@patch("app.main.client.models.generate_content")
def test_review_empty_response(mock_generate_content,valid_manifest):
    fake_response = Mock()
    fake_response.text = ""
    mock_generate_content.return_value = fake_response
    client = TestClient(app)
    response = client.post("/review", json = {
        "manifest" : yaml.dump(valid_manifest)
    })
    assert response.json()["detail"] == "Gemini returned an empty response"
    assert response.status_code == 500