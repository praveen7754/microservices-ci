#!/usr/bin/env bash
set -euo pipefail

# Usage: ./create-oidc-and-role.sh <AWS_ACCOUNT_ID> <AWS_REGION> <OWNER/REPO> <IMAGE_PREFIX>
# Example: ./create-oidc-and-role.sh 123456789012 us-east-1 myorg/myrepo myapp-

ACCOUNT_ID="$1"
REGION="$2"
REPO="$3"
IMAGE_PREFIX="$4"

# OIDC provider details
OIDC_URL="https://token.actions.githubusercontent.com"
# You must obtain the GitHub Actions OIDC thumbprint for token.actions.githubusercontent.com (public docs)
THUMBPRINT="<THUMBPRINT>"

echo "Creating OIDC provider (if not exists)..."
aws iam create-open-id-connect-provider \
  --url "$OIDC_URL" \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list "$THUMBPRINT" || true

ROLE_NAME="github-actions-ecr-role"
TRUST_POLICY_FILE="trust-policy.tmp.json"
cat > "$TRUST_POLICY_FILE" <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::${ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
          "token.actions.githubusercontent.com:sub": "repo:${REPO}:ref:refs/heads/main"
        }
      }
    }
  ]
}
EOF

echo "Creating role $ROLE_NAME"
aws iam create-role --role-name "$ROLE_NAME" --assume-role-policy-document file://"$TRUST_POLICY_FILE" || true

POLICY_NAME="github-actions-ecr-policy"
POLICY_FILE="ecr-policy.tmp.json"
cat > "$POLICY_FILE" <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["ecr:GetAuthorizationToken"],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "ecr:PutImage",
        "ecr:BatchCheckLayerAvailability"
      ],
      "Resource": "arn:aws:ecr:${REGION}:${ACCOUNT_ID}:repository/${IMAGE_PREFIX}*"
    },
    {
      "Effect": "Allow",
      "Action": ["ecr:CreateRepository"],
      "Resource": "*",
      "Condition": { "StringEquals": { "aws:RequestedRegion": "${REGION}" } }
    }
  ]
}
EOF

echo "Putting role policy"
aws iam put-role-policy --role-name "$ROLE_NAME" --policy-name "$POLICY_NAME" --policy-document file://"$POLICY_FILE"

ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"

echo "Created/ensured role: $ROLE_ARN"
echo "Set repository secret AWS_ROLE_TO_ASSUME to this value in GitHub: $ROLE_ARN"

echo "Cleaning up temp files"
rm -f "$TRUST_POLICY_FILE" "$POLICY_FILE"

echo "Done."
