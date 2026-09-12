"""Prevent the temporary proof package from acquiring broader cloud privileges."""

import json
from pathlib import Path


def test_proof_policy_remains_scoped_and_cannot_start_itself():
    template = json.loads(Path("infra/bedrock-proof.json").read_text())
    resources = template["Resources"]
    assert {r["Type"] for r in resources.values()} == {
        "AWS::CodeBuild::Project",
        "AWS::IAM::Role",
        "AWS::Logs::LogGroup",
    }
    assert len(resources) == 3
    role = resources["ProofRole"]["Properties"]
    trust = role["AssumeRolePolicyDocument"]["Statement"]
    assert len(trust) == 1
    assert trust[0]["Principal"] == {"Service": "codebuild.amazonaws.com"}
    conditions = trust[0]["Condition"]
    assert conditions["StringEquals"]["aws:SourceAccount"] == {"Ref": "AWS::AccountId"}
    assert conditions["ArnEquals"]["aws:SourceArn"]["Fn::Sub"].endswith(
        ":project/${AWS::StackName}-proof"
    )
    assert not role.get("ManagedPolicyArns")
    statements = [s for p in role["Policies"] for s in p["PolicyDocument"]["Statement"]]
    assert len(statements) == 2
    assert all(s["Effect"] == "Allow" for s in statements)
    model, logs = statements
    assert model["Action"] == ["bedrock:InvokeModel"]
    assert model["Resource"] == (
        "arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-micro-v1:0"
    )
    assert set(logs["Action"]) == {"logs:CreateLogStream", "logs:PutLogEvents"}
    assert logs["Resource"]["Fn::Sub"] == (
        "arn:${AWS::Partition}:logs:${AWS::Region}:${AWS::AccountId}:"
        "log-group:/hestiarelay/${AWS::StackName}:log-stream:*"
    )
    project = resources["ProofProject"]["Properties"]
    assert not project.get("Triggers")
    assert project["AutoRetryLimit"] == 0
    assert project["ConcurrentBuildLimit"] == 1
    assert project["TimeoutInMinutes"] <= 10
    assert project["Environment"]["PrivilegedMode"] is False
    variables = {v["Name"]: v["Value"] for v in project["Environment"]["EnvironmentVariables"]}
    assert variables["HESTIA_EXECUTION_APPROVED"] == "NO"
    assert variables["HESTIA_SOURCE_COMMIT"] == {"Ref": "SourceCommit"}
    assert variables["HESTIA_REQUEST_SHA256"] == {"Ref": "RequestSha256"}
    assert resources["ProofLogGroup"]["Properties"]["RetentionInDays"] == 1
