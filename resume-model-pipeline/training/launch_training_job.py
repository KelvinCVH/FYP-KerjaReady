"""
Run train_rating_model.py as a SageMaker training job on GPU
Uploads the splits and the training code to 3, starts the job and prints the epoch result and the S3 path on the trained model
"""

import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import boto3

HERE = Path(__file__).resolve().parent
CODE_FILES = ["rating_model.py", "rating_metrics.py", "train_rating_model.py", "requirements.txt"]
DEFAULT_IMAGE = "550225433462.dkr.ecr.ap-southeast-5.amazonaws.com/pytorch:2.12.1-cu130-amzn2023-sagemaker"

RUN_SCRIPT = """#!/bin/bash
set -euo pipefail
cd /opt/ml/input/data/code
PY=""
for p in python python3; do
  if command -v "$p" >/dev/null && "$p" -c "import torch" 2>/dev/null; then PY="$p"; break; fi
done
if [ -z "$PY" ]; then echo "No Python with torch found in the image"; exit 1; fi
"$PY" --version
"$PY" -m pip install --quiet -r requirements.txt
exec "$PY" train_rating_model.py \\
  --train /opt/ml/input/data/train/train.csv \\
  --val /opt/ml/input/data/val/val.csv \\
  --model-dir /opt/ml/model "$@"
"""

def ensure_bucket(s3, bucket, region):
    try:
        s3.head_bucket(Bucket=bucket)
    except s3.exceptions.ClientError:
        print(f"Creating bucket {bucket}")
        s3.create_bucket(Bucket=bucket, CreateBucketConfiguration={"LocationConstraint": region})

def upload(s3, bucket, job_name, splits_dir):
    prefix = f"rating-model/{job_name}"
    for split in ["train", "val"]:
        s3.upload_file(str(Path(splits_dir) / f"{split}.csv"), bucket , f"{prefix}/{split}/{split}.csv")
    for name in CODE_FILES:
        s3.upload_file(str(HERE / name), bucket, f"{prefix}/code/{name}")
    s3.put_object(Bucket=bucket, Key=f"{prefix}/code/run_training.sh", Body=RUN_SCRIPT.encode())
    return f"s3://{bucket}/{prefix}"

def channel(name, uri):
    return{
        "ChannelName": name, 
        "InputMode": "File",
        "DataSource": {
           "S3DataSource": {
              "S3DataType": "S3Prefix",
              "S3Uri": uri,
              "S3DataDistributionType": "FullyReplicated"
           }
        }
    }

def print_log_tail(logs, job_name, lines=60):
    group = "/aws/sagemaker/TrainingJobs"
    try:
        streams = logs.describe_log_streams(logGroupName=group, logStreamNamePrefix=job_name)["logStreams"]
        for stream in streams:
            events = logs.get_log_events(logGroupName=group, logStreamName=stream["logStreamName"],
                                         limit=lines, startFromHead=False)["events"]
            print(f"\n--- last {len(events)} log lines ({stream['logStreamName']}) ---")
            for e in events:
                print(e["message"])
    except Exception as e:
        print(f"(Could not read the logs: {e}. Open CloudWatch logs > {group} > {job_name}.)")

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--role-arn", required=True, help="SageMaker execution role")
    p.add_argument("--profile", default="kerjaready")
    p.add_argument("--region", default="ap-southeast-5")
    p.add_argument("--splits-dir", default="data/splits")
    p.add_argument("--instance-type", default="ml.g6.xlarge")
    p.add_argument("--image", default=DEFAULT_IMAGE)
    p.add_argument("--epochs", default="6")
    p.add_argument("--max-hours", type=float, default=3)
    p.add_argument("--no-wait", action="store_true")
    args = p.parse_args(argv)

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    account = session.client("sts").get_caller_identity()["Account"]
    s3, sm, logs = session.client("s3"), session.client("sagemaker"), session.client("logs")
    bucket = f"kerjaready-sagemaker-training-{account}"
    job_name = "kerjaready-rating-model-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")

    ensure_bucket(s3, bucket, args.region)
    base = upload(s3, bucket, job_name, args.splits_dir)
    sm.create_training_job(
        TrainingJobName=job_name,
        RoleArn=args.role_arn,
        AlgorithmSpecification={
            "TrainingImage": args.image,
            "TrainingInputMode": "File",
            "ContainerEntrypoint": ["bash", "/opt/ml/input/data/code/run_training.sh"],
            "ContainerArguments": ["--epochs", str(args.epochs)],
        },
        InputDataConfig=[channel("train", f"{base}/train/"), channel("val", f"{base}/val/"), channel("code", f"{base}/code/")],
        OutputDataConfig={"S3OutputPath": f"s3://{bucket}/rating-model/output/"},
        ResourceConfig={"InstanceType": args.instance_type, "InstanceCount": 1, "VolumeSizeInGB": 30},
        StoppingCondition={"MaxRuntimeInSeconds": int(args.max_hours * 3600)},
    )
    print(f"Started {job_name} on {args.instance_type}. Inputs and code in {base}/")
    if args.no_wait:
        return
    
    last = None
    while True:
        job = sm.describe_training_job(TrainingJobName=job_name)
        state = (job["TrainingJobStatus"], job.get("SecondaryStatus"))
        if state != last:
            print(f" {datetime.now().strftime('%H:%M:%S')} {state[0]} / {state[1]}")
            last = state
        if job["TrainingJobStatus"] in ("Completed", "Failed", "Stopped"):
            break
        time.sleep(60)

    print_log_tail(logs, job_name)
    if job["TrainingJobStatus"] != "Completed":
        sys.exit(f"\nJob {job['TrainingJobStatus']}: {job.get('FailureReason', 'no reason given')}")
    print(f"\nModel: {job['ModelArtifacts']['S3ModelArtifacts']}")
    print(f"Billable time: {job.get('BillableTimeInSeconds', 0) // 60} min")

if __name__ == "__main__":
    main()

