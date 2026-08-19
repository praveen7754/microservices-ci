# CI changes

- Builds and tests gateway, auth, product, order, cart, and frontend.
- Pushes all six application images to the `microservices-1` ECR repository.
- Uses AWS OIDC; no long-lived AWS access keys are required by the workflow.
- Publishes both stable service tags and commit-specific tags.
- Kafka is not required by CI in the current stage.
- Redis is a runtime dependency for the cart and product services and is deployed by the CD Helm chart.
