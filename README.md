# Flask Microservices E-commerce CI

Services/images:

- gateway
- auth
- product
- order
- cart
- frontend

The GitHub Actions workflow tests the Python services and builds/pushes all six
Docker images to Amazon ECR.

Current runtime architecture is intentionally staged:

- Kubernetes / Argo CD deploys the application images.
- Redis is used by cart and product and has persistent storage in the CD chart.
- Product application data has a persistent PVC.
- Kafka is intentionally deferred to a later stage.
