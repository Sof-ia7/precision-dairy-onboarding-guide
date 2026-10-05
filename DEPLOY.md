# Deploying on Geddes (Purdue RCAC)

Geddes runs **Kubernetes managed by Rancher**. You need a Purdue account with access to a Geddes **namespace**. Within your own namespace you can deploy everything yourself through the Rancher UI or `kubectl`; IT does not need to do it for you.

Before starting, fill in every `REPLACE` placeholder in `deploy/`. [HANDOFF.md](HANDOFF.md) explains where each value comes from.

---

## 0. Tools and access
1. Log in to the Rancher UI with your Purdue career account. The URL is in the RCAC Geddes docs.
2. Get `kubectl` working, by either:
   - using the **kubectl shell** button in the Rancher UI, or
   - downloading the **KubeConfig** file (Rancher UI, top right) to `~/.kube/config` on your computer.
3. Check access:
   ```bash
   kubectl config set-context --current --namespace=<your-namespace>
   kubectl get pods
   kubectl get storageclass        # pick the Ceph BLOCK class for the REPLACE placeholders
   ```

## 1. The image
CI builds the image and pushes it to **GHCR** on every push to `main`:
`ghcr.io/<owner>/precision-dairy-pipeline:sha-<commit>` (and `:latest`). Use a `sha-` tag in the CronJob so you always know which version runs.
- If the GHCR package is **private**, make it public (GitHub → Packages → Package settings), or create an image-pull secret.
- **Harbor alternative** (only from campus or the VPN): push to `geddes-registry.rcac.purdue.edu/<project>/precision-dairy-pipeline:<tag>`.
  ```bash
  podman login geddes-registry.rcac.purdue.edu        # same account as Rancher
  podman build --build-arg BASE=geddes-registry.rcac.purdue.edu/docker-hub-cache/library/python:3.11-slim -t precision-dairy-pipeline:<tag> .
  podman tag precision-dairy-pipeline:<tag> geddes-registry.rcac.purdue.edu/<project>/precision-dairy-pipeline:<tag>
  podman push geddes-registry.rcac.purdue.edu/<project>/precision-dairy-pipeline:<tag>
  ```
  For a **private** Harbor project:
  1. In Harbor, create a **pull-only robot account**. Copy its token immediately; Harbor cannot show it again.
  2. In Rancher, go to *Storage → Secrets → Create → Registry*.
  3. Use domain `geddes-registry.rcac.purdue.edu`, the robot's full name (`robot$...`) as the username and its token as the password. Name the secret `harbor-pull`.
  4. Uncomment `imagePullSecrets` in `deploy/20-pipeline-cronjob.yaml`.

**RCAC rule:** every Docker Hub image must be pulled through the cache, `geddes-registry.rcac.purdue.edu/docker-hub-cache/...`. The manifests already do this for `postgres` and `grafana`.

## 2. Secrets (never in git)
```bash
kubectl create secret generic dairy-db \
  --from-literal=POSTGRES_HOST=postgres \
  --from-literal=POSTGRES_PORT=5432 \
  --from-literal=POSTGRES_DB=dairy \
  --from-literal=POSTGRES_USER=dairy \
  --from-literal=POSTGRES_PASSWORD='<strong password>' \
  --from-literal=POSTGRES_SCHEMA=dairy \
  --from-literal=GRAFANA_DB_USER=grafana_reader \
  --from-literal=GRAFANA_DB_PASSWORD='<another password>' \
  --from-literal=GF_SECURITY_ADMIN_USER=admin \
  --from-literal=GF_SECURITY_ADMIN_PASSWORD='<admin password>'
```
(`deploy/templates/secrets.example.yaml` shows the same thing as YAML.) Save the passwords somewhere safe for the next maintainer, such as the lab's password manager.

## 3. ConfigMaps (from files in this repo)
```bash
kubectl create configmap postgres-init --from-file=postgres/init/ --dry-run=client -o yaml | kubectl apply -f -
kubectl create configmap grafana-datasources --from-file=grafana/provisioning/datasources/ --dry-run=client -o yaml | kubectl apply -f -
kubectl create configmap grafana-dashboard-provider --from-file=grafana/provisioning/dashboards/ --dry-run=client -o yaml | kubectl apply -f -
kubectl create configmap grafana-dashboards --from-file=grafana/dashboards/ --dry-run=client -o yaml | kubectl apply -f -
```
Re-run the last command whenever the dashboards change, then `kubectl rollout restart deployment/grafana`.

## 4. Apply the manifests
```bash
kubectl apply -f deploy/          # postgres, pipeline CronJob, grafana (templates/ is not applied)
kubectl get pods -w               # wait for postgres-0 and grafana-* to be Running
```
`postgres/init/01-roles.sh` runs **only on the first start with an empty volume**. It creates the `dairy` schema and the read-only `grafana_reader` role.

## 5. First run by hand
```bash
kubectl create job --from=cronjob/pipeline first-run
kubectl logs -f job/first-run
```
Expect "Chapter 3 pipeline complete", "Wrote N rows" for Chapter 4, "Loaded N rows into dairy.…" and "Workflow complete". If it fails, see Troubleshooting below.

Check the tables:
```bash
kubectl exec -it postgres-0 -- psql -U dairy -d dairy -c '\dt dairy.*'
```

## 6. Open Grafana
- With the Ingress: `https://<host from deploy/30-grafana.yaml>`
- Without an Ingress (testing): `kubectl port-forward svc/grafana 3000:3000`, then open http://localhost:3000

Log in with `GF_SECURITY_ADMIN_*`. The four dashboards are in the **Precision Dairy** folder. To let farm staff view without logging in, enable the anonymous Viewer settings in `deploy/30-grafana.yaml`, and only if the URL is not public.

## 7. Updating
- **Code:** push to `main` → CI builds `sha-<commit>` → set that tag in the CronJob → `kubectl apply -f deploy/20-pipeline-cronjob.yaml`.
- **Dashboards:** edit `grafana/build_dashboards.py` → `python grafana/build_dashboards.py` → step 3 (last command) → restart Grafana.
- **Nutrient table:** the nutritionist updates the Excel file. A CSV version must reach the path mounted as `CH4_NUTRIENT_TABLE`. See HANDOFF.md.

## Troubleshooting
| Symptom | Likely cause |
|---|---|
| `ImagePullBackOff` | wrong image/tag; private registry without a pull secret; Docker Hub image not pulled through `docker-hub-cache` |
| `No parquet files found in /depot/...` / `No files found` | wrong `CH3_*`/`CH4_*` path, or the Data Depot volume is not mounted |
| Pod is `Pending` | PVC not bound (wrong `storageClassName`) or the namespace quota is exceeded |
| CSVs written but no tables | `POSTGRES_HOST` missing from the secret, or a wrong password |
| Grafana panels say "relation does not exist" | the pipeline has not run yet, or a table was renamed |
| Grafana "permission denied" | the reader role was not created (the init script runs only on the first start). Run `01-roles.sh` by hand with `kubectl exec`. |
| Postgres `CrashLoopBackOff` on a fresh volume | the volume is not writable by uid 999; check `fsGroup` and the storage class |
