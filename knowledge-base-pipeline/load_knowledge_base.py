"""Load the knowledge base into Aurora through the RDS Data API.

Loads the skill vocabulary into skills, the cleaned postings into job_postings and the role profiles into
role_skills, in one transaction, so a failed load changes nothing. Postings and role profiles are replaced
on every run, so the script can be run again after the pipeline changes. Skills are only ever added,
because resumes and job listings may refer to them.

Usage:
    python knowledge-base-pipeline/load_knowledge_base.py data/clean/clean-job-postings.csv
        knowledge-base-pipeline/skill_vocabulary.csv data/clean/role-skills.csv
        --cluster-arn <arn> --secret-arn <arn> --database <name>
"""

import argparse
import time

import boto3
import pandas as pd

BATCH_SIZE = 500
RESUME_ATTEMPTS = 10
RESUME_WAIT_SECONDS = 5


def long_value(name, value):
    return {"name": name, "value": {"longValue": int(value)}}


def string_value(name, value, type_hint=None):
    parameter = {"name": name, "value": {"stringValue": str(value)}}
    if type_hint:
        parameter["typeHint"] = type_hint
    return parameter


class Transaction:
    """One Data API transaction: committed if every statement succeeds, otherwise rolled back."""

    def __init__(self, client, cluster_arn, secret_arn, database):
        self.client = client
        self.target = {"resourceArn": cluster_arn, "secretArn": secret_arn}
        self.database = database
        self.transaction_id = None

    def __enter__(self):
        # A cluster scaled to 0 ACU takes a few seconds to resume on the first call
        for _ in range(RESUME_ATTEMPTS):
            try:
                response = self.client.begin_transaction(**self.target, database=self.database)
                self.transaction_id = response["transactionId"]
                return self
            except self.client.exceptions.DatabaseResumingException:
                print("Database is resuming, waiting...")
                time.sleep(RESUME_WAIT_SECONDS)
        raise SystemExit("The database did not resume in time. Run the script again.")

    def __exit__(self, error_type, error, traceback):
        if error_type is None:
            self.client.commit_transaction(**self.target, transactionId=self.transaction_id)
        else:
            self.client.rollback_transaction(**self.target, transactionId=self.transaction_id)
            print("Load failed, so nothing was changed")

    def run(self, sql):
        """Run one statement and return its rows as lists of plain values."""
        response = self.client.execute_statement(
            **self.target, database=self.database, transactionId=self.transaction_id, sql=sql
        )
        return [[next(iter(field.values())) for field in record] for record in response.get("records", [])]

    def run_many(self, sql, parameter_sets):
        """Run one statement once per parameter set, in batches."""
        for start in range(0, len(parameter_sets), BATCH_SIZE):
            self.client.batch_execute_statement(
                **self.target,
                database=self.database,
                transactionId=self.transaction_id,
                sql=sql,
                parameterSets=parameter_sets[start : start + BATCH_SIZE],
            )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("cleaned_csv")
    parser.add_argument("vocabulary_csv")
    parser.add_argument("role_skills_csv")
    parser.add_argument("--cluster-arn", required=True)
    parser.add_argument("--secret-arn", required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--profile", help="AWS CLI profile; the default credentials are used if omitted")
    parser.add_argument("--region", default="ap-southeast-5")
    args = parser.parse_args()

    postings = pd.read_csv(args.cleaned_csv)
    skill_names = pd.read_csv(args.vocabulary_csv)["skill"]
    profiles = pd.read_csv(args.role_skills_csv)

    client = boto3.Session(profile_name=args.profile, region_name=args.region).client("rds-data")
    with Transaction(client, args.cluster_arn, args.secret_arn, args.database) as database:
        role_ids = dict(database.run("SELECT title, role_id FROM roles"))
        missing_roles = sorted(set(postings["role_title"]) - set(role_ids))
        if missing_roles:
            raise SystemExit(f"Roles not in the roles table, so apply migration 003 first: {', '.join(missing_roles)}")

        database.run_many(
            "INSERT INTO skills (name) VALUES (:name) ON CONFLICT (name) DO NOTHING",
            [[string_value("name", name)] for name in skill_names],
        )
        skill_ids = dict(database.run("SELECT name, skill_id FROM skills"))

        database.run("DELETE FROM role_skills")
        database.run("DELETE FROM job_postings")
        database.run_many(
            "INSERT INTO job_postings (posting_id, role_id, job_title, posted_date) "
            "VALUES (:posting_id, :role_id, :job_title, :posted_date)",
            [
                [
                    long_value("posting_id", job_id),
                    long_value("role_id", role_ids[role]),
                    string_value("job_title", job_title),
                    string_value("posted_date", listing_date, "DATE"),
                ]
                for job_id, role, job_title, listing_date in postings[
                    ["job_id", "role_title", "job_title", "listing_date"]
                ].itertuples(index=False)
            ],
        )
        database.run_many(
            "INSERT INTO role_skills (role_id, skill_id, demand_share) VALUES (:role_id, :skill_id, :demand_share)",
            [
                [
                    long_value("role_id", role_ids[role]),
                    long_value("skill_id", skill_ids[skill]),
                    string_value("demand_share", f"{share:.4f}", "DECIMAL"),
                ]
                for role, skill, share in profiles[["role_title", "skill", "demand_share"]].itertuples(index=False)
            ],
        )
        counts = database.run(
            "SELECT (SELECT count(*) FROM job_postings), (SELECT count(*) FROM skills), "
            "(SELECT count(*) FROM role_skills)"
        )[0]

    print(f"Loaded {counts[0]:,} job postings, {counts[1]:,} skills and {counts[2]:,} role-skill rows")


if __name__ == "__main__":
    main()