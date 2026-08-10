# Comprehensive Helm Templating & Syntax Guide

This guide explains the syntax, keywords, braces, functions, and scoping rules used in **Helm Templates (Go Templating Engine)** with practical examples drawn directly from this repository's Helm chart (`minikube/backend`).

---

## Table of Contents
1. [Braces Syntax & Whitespace Control (`{{` and `}}`)](#1-braces-syntax--whitespace-control--and-)
2. [Dot (`.`) Scoping & Built-in Objects](#2-dot--scoping--built-in-objects)
3. [Core Keywords & Control Flow](#3-core-keywords--control-flow)
4. [Pipelining (`|`) & Indentation Functions](#4-pipelining--indentation-functions)
5. [Useful Template Functions](#5-useful-template-functions)
6. [Named Templates (`_helpers.tpl`) & Reusability](#6-named-templates-_helperstpl--reusability)
7. [Annotated Examples from this Repository](#7-annotated-examples-from-this-repository)

---

## 1. Braces Syntax & Whitespace Control (`{{` and `}}`)

Helm uses the **Go `text/template` engine** extended with **Sprig template functions**.

### Basic Interpolation
Any statement enclosed in double curly braces `{{ ... }}` is evaluated by Helm during template rendering.
```yaml
name: {{ .Values.image.repository }}
```
**Rendered Output:**
```yaml
name: catalog-summarizer-backend
```

### Whitespace Chipping / Trimming (`{{-` and `-}}`)
In YAML, whitespace and newline management is critical. The hyphens inside braces strip whitespace:
- `{{- ` (Hyphen on the left) strips whitespace and newlines **before** the directive.
- ` -}}` (Hyphen on the right) strips whitespace and newlines **after** the directive.

#### Example Without Hyphens (`{{ ... }}`):
```yaml
  {{ if .Values.keda.enabled }}
  enabled: true
  {{ end }}
```
**Rendered Output** (creates empty blank lines in YAML):
```yaml

  enabled: true

```

#### Example With Hyphens (`{{- ... -}}`):
```yaml
  {{- if .Values.keda.enabled }}
  enabled: true
  {{- end }}
```
**Rendered Output** (clean YAML without blank lines):
```yaml
  enabled: true
```

---

## 2. Dot (`.`) Scoping & Built-in Objects

The dot (`.`) represents the **current scope/context**. At the root level of a template, `.` refers to the top-level Helm context.

### Top-Level Built-in Objects
| Object | Description | Example |
| :--- | :--- | :--- |
| `.Values` | Values passed from `values.yaml` or `--set` flags | `.Values.service.port` |
| `.Release` | Information about the current Helm release | `.Release.Name`, `.Release.Namespace` |
| `.Chart` | Metadata from `Chart.yaml` | `.Chart.Name`, `.Chart.Version`, `.Chart.AppVersion` |
| `.Template` | Information about the current template file being rendered | `.Template.Name` |
| `$` | Always references the **Root Context**, regardless of local scope | `$.Values.service.port` |

---

## 3. Core Keywords & Control Flow

### `if` / `else if` / `else` / `end`
Used for conditional rendering of YAML blocks.

```yaml
{{- if .Values.keda.enabled }}
# Rendered only when keda.enabled is true
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
{{- else if .Values.hpa.enabled }}
# Rendered when keda is false and hpa is true
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
{{- else }}
# Fallback
{{- end }}
```

#### Boolean Expressions (`and`, `or`, `not`, `eq`)
Helm functions use prefix notation: `function argument1 argument2`.

```yaml
# Checks if keda exists AND keda.enabled is true
{{- if and .Values.keda .Values.keda.enabled }}

# Checks if replicas should NOT be rendered
{{- if not (and .Values.keda .Values.keda.enabled) }}
replicas: {{ .Values.replicaCount }}
{{- end }}
```

---

### `with` / `end`
The `with` keyword changes the current scope (`.`) to the target object. If the object is empty (`nil` or `{}`), the entire `with` block is skipped.

```yaml
{{- with .Values.resources }}
resources:
  limits:
    cpu: {{ .limits.cpu }}    # Notice: . refers to .Values.resources now!
    memory: {{ .limits.memory }}
{{- end }}
```

---

### `range` / `end`
Used to loop over lists (slices) or key-value maps.

#### Iterating Over a List:
If `values.yaml` has:
```yaml
hosts:
  - catalog.local
  - api.local
```
Template code:
```yaml
hosts:
{{- range .Values.hosts }}
- {{ . | quote }}
{{- end }}
```
**Rendered Output:**
```yaml
hosts:
- "catalog.local"
- "api.local"
```

#### Accessing Root Scope Inside `range` or `with`:
Inside a `range` block, `.` becomes the individual array item. To access root values (like `.Release` or `.Values`), use `$` (Root Scope):

```yaml
{{- range .Values.ingress.hosts }}
  serviceName: {{ include "backend.fullname" $ }}  # $ refers to root context
  hostName: {{ .host }}                          # . refers to current host item
{{- end }}
```

---

## 4. Pipelining (`|`) & Indentation Functions

Helm supports UNIX-style pipelines `|` where the output of one expression is passed as the **last argument** of the next function.

### `nindent` vs `indent`
- `indent N`: Indents the string by `N` spaces.
- `nindent N`: Prepends a **newline** and indents the string by `N` spaces (essential for multi-line block inserts).

#### Example with `toYaml` and `nindent`:
In `values.yaml`:
```yaml
nodeSelector:
  disktype: ssd
  environment: production
```
In template (`deployment.yaml`):
```yaml
nodeSelector:
  {{- toYaml .Values.nodeSelector | nindent 2 }}
```
**Rendered Output:**
```yaml
nodeSelector:
  disktype: ssd
  environment: production
```

---

## 5. Useful Template Functions

| Function | Purpose | Example | Output |
| :--- | :--- | :--- | :--- |
| `default` | Fallback value if empty | `{{ .Values.name | default "backend" }}` | `"backend"` (if empty) |
| `toYaml` | Serializes Go struct/map to YAML | `{{ toYaml .Values.podAnnotations }}` | Formatted YAML |
| `quote` | Wraps string in double quotes | `{{ "8000" | quote }}` | `"8000"` |
| `trunc N` | Truncates string to `N` characters | `{{ "my-very-long-name" | trunc 10 }}` | `"my-very-lo"` |
| `trimSuffix` | Removes suffix if present | `{{ "backend-" | trimSuffix "-" }}` | `"backend"` |
| `printf` | Formats string using format verbs | `{{ printf "%s-svc" .Release.Name }}` | `"my-release-svc"` |

---

## 6. Named Templates (`_helpers.tpl`) & Reusability

Helm allows defining reusable template snippets in `_helpers.tpl`.

### Defining a Named Template (`define`)
In `templates/_helpers.tpl`:
```yaml
{{/*
Expand the full name of the chart.
*/}}
{{- define "backend.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
```

### Invoking a Named Template (`include` vs `template`)
Always use **`include`** instead of `template` because `include` allows pipelining output directly into indentation functions like `nindent`.

```yaml
metadata:
  name: {{ include "backend.fullname" . }}
  labels:
    {{- include "backend.labels" . | nindent 4 }}
```

---

## 7. Annotated Examples from this Repository

### Example 1: `scaledobject.yaml` (Conditional KEDA Autoscaler)
```yaml
1: {{- if and .Values.keda .Values.keda.enabled }}  # Only renders if keda section exists and is enabled
2: apiVersion: keda.sh/v1alpha1
3: kind: ScaledObject
4: metadata:
5:   name: {{ include "backend.fullname" . }}          # Calls helper function to generate resource name
6:   labels:
7:     {{- include "backend.labels" . | nindent 4 }}   # Calls helper for common labels and indents 4 spaces
8: spec:
9:   scaleTargetRef:
10:     apiVersion: apps/v1
11:     kind: Deployment
12:     name: {{ include "backend.fullname" . }}
13:   minReplicaCount: {{ .Values.keda.minReplicaCount | default 1 }}  # Uses default 1 if not set
14:   maxReplicaCount: {{ .Values.keda.maxReplicaCount | default 10 }} # Uses default 10 if not set
15:   pollingInterval: {{ .Values.keda.pollingInterval | default 15 }}
16:   cooldownPeriod: {{ .Values.keda.cooldownPeriod | default 60 }}
17:   {{- with .Values.keda.advanced }}                             # Changes scope to .Values.keda.advanced if present
18:   advanced:
19:     {{- toYaml . | nindent 4 }}                                 # Converts dictionary to YAML at 4-space indent
20:   {{- end }}
21:   triggers:
22:     {{- toYaml .Values.keda.triggers | nindent 4 }}             # Converts triggers list to YAML at 4-space indent
23: {{- end }}                                                      # Closes the top-level `if` statement
```

---

### Example 2: `deployment.yaml` (KEDA-aware Replicas & Probes)
```yaml
spec:
  # Suppresses replicas field when KEDA is enabled so KEDA owns scaling
  {{- if not (and .Values.keda .Values.keda.enabled) }}
  replicas: {{ .Values.replicaCount }}
  {{- end }}
  
  containers:
    - name: {{ .Chart.Name }}
      image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
      
      # Injects environment variables from my-secret
      {{- with .Values.envFrom }}
      envFrom:
        {{- toYaml . | nindent 12 }}
      {{- end }}
```

---

### Quick Reference Cheatsheet

| Syntax | Description |
| :--- | :--- |
| `{{ .Values.foo }}` | Print value of `foo` from `values.yaml` |
| `{{-` / `-}}` | Trim whitespace before / after directive |
| `{{- if .Values.enabled }}` | Conditional start |
| `{{- with .Values.config }}` | Change context (`.`) to `.Values.config` |
| `{{- range .Values.items }}` | Loop over `.Values.items` |
| `{{- end }}` | Close `if`, `with`, or `range` block |
| `{{ toYaml . | nindent 4 }}` | Convert object to YAML and indent by 4 spaces |
| `{{ include "name" . }}` | Include named template with scope `.` |
