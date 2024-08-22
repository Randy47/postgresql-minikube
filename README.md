# Deploy a small Kubernetes cluster in your local environment.
Create a 3-Node PostgreSQL Cluster
1. Add Bitnami Helm Repository
First, ensure you have the Bitnami Helm repository added:
`helm repo add bitnami https://charts.bitnami.com/bitnami`
`helm repo update`
2. Create a Namespace (Optional)
Create a namespace to keep your PostgreSQL cluster isolated:
`kubectl create namespace postgresql-cluster`
3. Install the Helm Chart
`helm install postgresql-cluster bitnami/postgresql-ha   --namespace postgresql-cluster`
 
4. Verify the Installation
Check the status of your deployment:
`kubectl get pods -n postgresql-cluster
kubectl get services -n postgresql-cluster`
You should see multiple PostgreSQL pods, including primary and replica nodes, and a LoadBalancer service for accessing the PostgreSQL cluster.
 
 
5. Create a simple database with two related tables using a foreign key
	Create database and schema
`CREATE DATABASE irmtestdb;
\c irmtestdb
CREATE TABLE teacher (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);
CREATE TABLE student (
    id SERIAL PRIMARY KEY,
	student_name TEXT,
    teacher_id INT REFERENCES teacher(id),
    course TEXT
);`

	Configure connection from outside the cluster execute the following command:
To connect to your database from outside the cluster execute the following commands:
`kubectl port-forward --namespace postgresql-cluster svc/postgresql-cluster-postgresql-ha-pgpool 5441:5432 &
psql -h 127.0.0.1 -p 5441 -U postgres -d postgres`
6. Insert 100,000 Records Using Faker
Install Python and Libraries:
`pip install psycopg2 faker`
Python Script to Insert Records:
`import psycopg2
from faker import Faker

conn = psycopg2.connect(
    dbname="irmtestdb", user="postgres", password="hXEXiNCbCs", host="127.0.0.1", port="5441"
)
cursor = conn.cursor()

fake = Faker()

for _ in range(100000):
    cursor.execute("INSERT INTO teacher (name) VALUES (%s) RETURNING id", (fake.name(),))
    teacher_id = cursor.fetchone()[0]
    cursor.execute(
        "INSERT INTO student (teacher_id, student_name, course) VALUES (%s, %s, %s)",
        (teacher_id, fake.name(), fake.text()),
    )
conn.commit()
cursor.close()
conn.close()`
`python3 sampledb.py`

Deploy a Standalone PostgreSQL Instance
Create a separate namespace for the standalone instance:
`kubectl create namespace postgresql-standalone`
Deploy using Helm:
`helm install postgresql-standalone bitnami/postgresql --namespace postgresql-standalone`
Set Up Asynchronous Replication:
Configure postgresql.conf on the Primary Cluster
Create or edit values.yaml:
```
persistence:
  enabled: true
  size: 8Gi

patroni:
  postgresql:
    parameters:
      wal_level: "replica"
      max_wal_senders: 10
      max_replication_slots: 5
      wal_keep_segments: 8
      archive_command: 'cp %p /bitnami/postgresql/data/wal_archive/%f'
  replicationMode: "sync"
volumePermissions:
  enabled: true
Apply changes using Helm:
helm upgrade postgresql-cluster bitnami/postgresql \
  --namespace postgresql-cluster \
  --values values.yaml
```

Ensure Configuration Persistence
Sometimes, configurations are managed through Kubernetes ConfigMaps or Secrets, especially with Helm. Check if your Helm chart uses a ConfigMap to manage PostgreSQL configurations:
List and describe the ConfigMap:
`kubectl get configmap -n postgresql-cluster
kubectl describe configmap postgresql-cluster-postgresql-ha-postgresql-hooks-scripts -n postgresql-cluster`
Configure postgresql.conf on the Postgresql Standalone
Create or edit standalone-values.yaml:
```
postgresqlUsername: "replica_u"
postgresqlPassword: "replica_u"
postgresqlDatabase: "irmtestdb"
persistence:
  enabled: true
  size: 8Gi
  
volumePermissions:
  enabled: true
```
Access the replica pod:
`kubectl exec -it standalone-postgresql-0 -n postgres-standalone -- /bin/bash`
Stop the PostgreSQL service:
`pg_ctl -D /bitnami/postgresql/data stop`
Clear out the existing data directory:
`rm -rf /bitnami/postgresql/data/*`
Perform a base backup from the primary cluster leader:
On the replica
`pg_basebackup -h 10.244.0.133 -D /bitnami/postgresql/data -U repmgr -v -P --wal-method=stream`
Create the recovery.conf in the replica with the following content:
`cat > /bitnami/postgresql/data/recovery.conf <<EOF
standby_mode = 'on'
primary_conninfo = 'host=<primary-cluster-ip> port=5432 user=replicator password=replicator_password'
primary_slot_name = 'replica_slot'
trigger_file = '/tmp/postgresql.trigger'
EOF`
Start the PostgreSQL service on the replica:
`pg_ctl -D /bitnami/postgresql/data start`
