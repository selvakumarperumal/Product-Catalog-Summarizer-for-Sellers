# Complete Minikube Deployment Guide for Product Catalog Summarizer

This step-by-step guide explains how to set up a local **Minikube** cluster, install all required dependencies (**Kubernetes Gateway API CRDs**, **Istio Service Mesh**, and **KEDA Autoscaler**), build/load the container image, and deploy the application using either **Standalone Manifests** or the **Helm Chart**.

---

## Table of Contents
1. [Prerequisites](#1-prerequisites)
2. [Step 1: Start Minikube & Enable Addons](#step-1-start-minikube--enable-addons)
3. [Step 2: Build & Load Backend Container Image](#step-2-build--load-backend-container-image)
4. [Step 3: Install Cluster Prerequisites (Gateway API, Istio, KEDA)](#step-3-install-cluster-prerequisites-gateway-api-istio-keda)
5. [Step 4: Create Kubernetes Secrets](#step-4-create-kubernetes-secrets)
6. [Step 5A: Deploy via Standalone Manifest (`keda-backend-simple.yaml`)](#step-5a-deploy-via-standalone-manifest-keda-backend-simpleyaml)
7. [Step 5B: Deploy via Helm Chart (`minikube/backend`)](#step-5b-deploy-via-helm-chart-minikubebackend)
8. [Step 6: Access the Application via Istio Gateway API](#step-6-access-the-application-via-istio-gateway-api)
9. [Step 7: Verification & Autoscaling Load Testing](#step-7-verification--autoscaling-load-testing)
10. [Step 8: Cleanup & Teardown](#step-8-cleanup--teardown)

---

## 1. Prerequisites

Ensure the following tools are installed on your workstation:
- **Minikube** (v1.30+)
- **kubectl** (v1.26+)
- **Helm** (v3.10+)
- **Docker** or **Podman**
- **istioctl** (Istio CLI)

---

## Step 1: Start Minikube & Enable Addons

Start a fresh Minikube cluster with sufficient CPU and memory allocation to run Istio, KEDA, and the backend application:

```bash
# Start Minikube with 4 CPUs and 4GB RAM
minikube start --cpus=4 --memory=4096 --driver=docker

# Enable essential addons
minikube addons enable metrics-server
```

Verify Minikube cluster status:
```bash
minikube status
kubectl get nodes
```

---

## Step 2: Build & Load Backend Container Image

Build the backend container image and make it available inside Minikube's internal Docker daemon.

### Option A: Build Directly Inside Minikube Docker Environment (Recommended)
Point your shell's Docker CLI to Minikube's internal Docker daemon:

```bash
# Set shell environment to use Minikube's Docker daemon
eval $(minikube -p minikube docker-env)

# Build the Docker image (from the root of the repository)
docker build -t catalog-summarizer-backend:latest ./backend
```

### Option B: Build Locally & Load into Minikube
If building with host Docker:
```bash
# Build locally
docker build -t catalog-summarizer-backend:latest ./backend

# Load image into Minikube cluster
minikube image load catalog-summarizer-backend:latest
```

Verify the image is present inside Minikube:
```bash
minikube image ls | grep catalog-summarizer-backend
```

---

## Step 3: Install Cluster Prerequisites (Gateway API, Istio, KEDA)

The backend deployment relies on **Kubernetes Gateway API**, **Istio**, and **KEDA**. Install these cluster-wide dependencies:

### 1. Install Kubernetes Gateway API Standard CRDs
```bash
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.0.0/standard-install.yaml
```

### 2. Install Istio Service Mesh

You can install Istio using **Helm** (recommended for GitOps and Helm workflows) or **istioctl** CLI:

#### Option A: Install Istio using Helm (Recommended)
```bash
# Add Istio Helm repository
helm repo add istio https://istio-release.storage.googleapis.com/charts
helm repo update

# Create namespace for Istio control plane
kubectl create namespace istio-system

# Step A1: Install Istio Base (CRDs and ClusterRoles)
helm install istio-base istio/base -n istio-system --set defaultRevision=default

# Step A2: Install Istio Control Plane (istiod)
helm install istiod istio/istiod -n istio-system --wait

# Enable automatic Istio sidecar injection in the default namespace (optional)
kubectl label namespace default istio-injection=enabled
```

#### Option B: Install Istio using `istioctl` CLI (Alternative Developer Install)
```bash
# Install Istio using istioctl CLI
istioctl install --set profile=default -y

# Enable automatic Istio sidecar injection in the default namespace (optional)
kubectl label namespace default istio-injection=enabled
```

### 3. Install KEDA (Kubernetes Event-driven Autoscaling)
```bash
# Add KEDA Helm repository
helm repo add keda https://kedacore.github.io/charts
helm repo update

# Install KEDA into namespace keda
helm install keda keda/keda --namespace keda --create-namespace
```

Verify all operators and CRDs are running:
```bash
# Verify KEDA operator status
kubectl get pods -n keda

# Verify Istio status
kubectl get pods -n istio-system

# Verify Gateway API CRDs installed
kubectl get crd | grep gateway.networking.k8s.io
```

---

## Step 4: Create Kubernetes Secrets

The backend container mounts environment secrets (like `GOOGLE_API_KEY`) from a Kubernetes Secret named `my-secret`.

Create `my-secret` using your local `.env` file:

```bash
# Ensure .env file exists in project root
kubectl create secret generic my-secret --from-env-file=.env
```

Verify the secret was created:
```bash
kubectl get secret my-secret
```

---

## Step 5A: Deploy via Standalone Manifest (`keda-backend-simple.yaml`)

If you want to deploy using the all-in-one single manifest:

```bash
# Apply the unified manifest
kubectl apply -f minikube/keda-backend-simple.yaml
```

This single command deploys:
1. `Deployment` (`catalog-summarizer-backend`)
2. `Service` (`catalog-summarizer-backend-svc`)
3. `ScaledObject` (`catalog-summarizer-scaler`)
4. `GatewayClass` (`istio`)
5. `Gateway` (`catalog-summarizer-gateway`)
6. `HTTPRoute` (`catalog-summarizer-httproute`)

---

## Step 5B: Deploy via Helm Chart (`minikube/backend`)

Alternatively, deploy using the customizable Helm chart:

```bash
# Lint the Helm chart to verify syntax
helm lint minikube/backend

# Install or upgrade the backend release
helm upgrade --install backend minikube/backend
```

### Overriding Values at Install Time
You can customize settings on the command line:
```bash
helm upgrade --install backend minikube/backend \
  --set keda.maxReplicaCount=5 \
  --set resources.requests.cpu=200m
```

---

## Step 6: Access the Application via Istio Gateway API

Minikube runs in an isolated network environment. To route traffic to the Istio Gateway:

### 1. Open Minikube Tunnel (In a separate terminal window)
```bash
minikube tunnel
```

### 2. Retrieve Gateway IP Address

First check your active Gateway name (`kubectl get gateway -n default`):

- **If deployed via Helm (`helm upgrade --install backend ...`)**:
  ```bash
  export GATEWAY_IP=$(kubectl get gateway backend-gateway -n default -o jsonpath='{.status.addresses[0].value}')
  echo "Gateway IP: $GATEWAY_IP"
  ```

- **If deployed via Standalone Manifest (`keda-backend-simple.yaml`)**:
  ```bash
  export GATEWAY_IP=$(kubectl get gateway catalog-summarizer-gateway -n default -o jsonpath='{.status.addresses[0].value}')
  echo "Gateway IP: $GATEWAY_IP"
  ```

- **Universal Command (Fetches the first active Gateway IP)**:
  ```bash
  export GATEWAY_IP=$(kubectl get gateway -n default -o jsonpath='{.items[0].status.addresses[0].value}')
  echo "Gateway IP: $GATEWAY_IP"
  ```

### 3. Test Health Endpoint
```bash
# Test the backend health endpoint
curl -i http://$GATEWAY_IP/api/v1/health
```

**Expected Response:**
```json
HTTP/1.1 200 OK
content-type: application/json

{"status":"ok","version":"1.0.0"}
```

### 4. Test Catalog Summarization Endpoint (`/api/v1/summarize`)

Upload a product catalog CSV file (`backend/test_catalog.csv`) to test the LLM summarization pipeline and save the resulting CSV output:

```bash
# Post test CSV catalog file and output summarized CSV
curl -X POST "http://$GATEWAY_IP/api/v1/summarize" \
  -F "file=@backend/test_catalog.csv" \
  --output output_summary.csv
```

Inspect the returned summarized CSV:
```bash
cat output_summary.csv
```

---

## Step 7: Verification & Autoscaling Load Testing

### 1. Check Workload & Scaling Status
```bash
# View active pods
kubectl get pods -l app=catalog-summarizer-backend

# Check KEDA ScaledObject status
kubectl get scaledobject catalog-summarizer-scaler

# Check Gateway API status
kubectl get gateway,httproute
```

### 2. Simulate Load to Test KEDA Autoscaling
Generate load against the health endpoint to trigger CPU autoscaling:

```bash
# Run a temporary load generator pod
kubectl run -i --tty load-generator --rm --image=busybox:1.28 --restart=Never -- \
  /bin/sh -c "while true; do wget -q -O- http://catalog-summarizer-backend-svc/api/v1/health; done"
```

In another terminal, watch KEDA scale up pods from 1 to 3 replicas:
```bash
kubectl get pods -l app=catalog-summarizer-backend -w
```

---

## Step 8: Cleanup & Teardown

### Teardown Standalone Manifest
```bash
kubectl delete -f minikube/keda-backend-simple.yaml
kubectl delete secret my-secret
```

### Teardown Helm Release
```bash
helm uninstall backend
kubectl delete secret my-secret
```

### Stop / Delete Minikube Cluster
```bash
minikube stop
# Optional: minikube delete
```
