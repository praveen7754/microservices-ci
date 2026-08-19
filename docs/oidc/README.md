OIDC setup for GitHub Actions -> AWS (ECR)

Follow these steps to configure OIDC-based access from GitHub Actions to AWS, restricted to your repository and the `main` branch.

1. Obtain the thumbprint for `token.actions.githubusercontent.com` (see GitHub docs) and set it in the script `create-oidc-and-role.sh` or pass it when running.

2. Run the included script to create the OIDC provider and role (replace arguments):

```bash
./create-oidc-and-role.sh <AWS_ACCOUNT_ID> <AWS_REGION> <OWNER/REPO> <IMAGE_PREFIX>
```

Example:

```bash
./create-oidc-and-role.sh 123456789012 us-east-1 myorg/myrepo myapp-
```

3. In GitHub repository Settings → Secrets → Actions add the secret:
- `AWS_ROLE_TO_ASSUME` = the role ARN printed by the script
- `AWS_REGION` = your region (e.g. `us-east-1`)
- `AWS_ACCOUNT_ID` = your account ID
- optionally `IMAGE_PREFIX` = prefix used for ECR repository names

4. Our workflow expects the role to be restricted to the `main` branch per the trust policy. If you need other branches, edit the trust policy accordingly.

Security notes:
- The role is only assumable by GitHub's OIDC provider and only for `repo:OWNER/REPO:ref:refs/heads/main`.
- Do not store long-lived AWS access keys in GitHub secrets when using OIDC.
