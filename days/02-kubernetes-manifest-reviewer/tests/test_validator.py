import pytest
from app.main import validate_yaml_refactored


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
def test_valid_manifest(valid_manifest):
    issues = validate_yaml_refactored(valid_manifest)
    print(issues)
    assert issues.issues == []



def test_missisng_kind(valid_manifest):
    manifest = valid_manifest.copy()
    manifest.pop("kind")
    issues = validate_yaml_refactored(manifest)
    print(issues)
    assert issues.issues == ["missing kind"]


def test_missing_metadata(valid_manifest):
    manifest = valid_manifest.copy()
    manifest.pop("metadata")
    issues = validate_yaml_refactored(manifest)
    print(issues)
    assert issues.issues == ["missing metadata"]

def test_missing_metadata_name(valid_manifest):
    manifest = valid_manifest.copy()
    manifest["metadata"].pop("name")
    issues = validate_yaml_refactored(manifest)
    print(issues)


def test_missing_spec(valid_manifest):
    manifest = valid_manifest.copy()
    manifest.pop("spec")
    issues = validate_yaml_refactored(manifest)
    print(issues)
    assert issues.issues == ["missing spec"]


def test_missing_spec_template(valid_manifest):
    manifest = valid_manifest.copy()
    manifest["spec"].pop("template")
    issues = validate_yaml_refactored(manifest)
    print(issues)
    assert issues.issues == ["missing spec.template"]



def test_missing_spec_template_spec(valid_manifest):
    manifest = valid_manifest.copy()
    manifest["spec"]["template"].pop("spec")
    issues = validate_yaml_refactored(manifest)
    print(issues)
    assert issues.issues == ["missing spec.template.spec"]


def test_missing_spec_template_spec_containers(valid_manifest):
    manifest = valid_manifest.copy()
    manifest["spec"]["template"]["spec"].pop("containers")
    issues = validate_yaml_refactored(manifest)
    print(issues)
    assert issues.issues == ["missing spec.template.spec.containers"]