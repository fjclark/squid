"""Functionality for interacting with the slurm queue."""

from dataclasses import dataclass
import subprocess
import os
import re
from typing import List
from ._errors import SlurmQueueReadError

# Mapping between display names and slurm attribute names
NAMES_TO_JOB_ATTRIBUTES = {
    "Name": "name",
    "Partition": "partition",
    "State": "state",
    "Time": "time_used",
    "Node/Reason": "node_list",
    "Submit Time": "submit_time",
    "Start Time": "start_time",
    "Job ID": "job_id",
    "Max End Time": "end_time",
    "Array Job Id": "array_job_id",
    "Array Task Id": "array_task_id",
}


@dataclass
class SlurmJob:
    """Dataclass to hold information about a slurm job."""

    job_id: str
    name: str
    partition: str
    time_used: str
    submit_time: str
    start_time: str
    end_time: str
    state: str
    array_job_id: str
    array_task_id: str
    node_list: str

    def __str__(self):
        """Format nicely into columns."""
        # Remove the year part of the times to save space
        times = [
            time.split("-")[-1]
            for time in [self.submit_time, self.start_time, self.end_time]
        ]
        return f"{self.job_id:<10}{self.name:<20}{self.partition:<25}{self.time_used:<10}{times[0]:<15}{times[1]:<15}{times[2]:<15}{self.state:<11}{self.node_list:<16}{self.array_job_id:<10}{self.array_task_id:<10}"


class SlurmQueue:
    """Class for interacting with the slurm queue."""

    def __init__(self):
        self.jobs = []
        self.update()

    def update(self, job_filter_attribute: str = "", job_filter_regex: str = ""):
        """Update the queue information."""
        self.jobs = []
        # Get the queue information
        queue_info = subprocess.check_output(
            [
                "squeue",
                "-u",
                f"{os.getlogin()}",
                # "chenfeng",
                "--noheader",
                "--array",
                "--Format",
                # Make sure output is well-spaced to prevent issues with parsing.
                "JobID:1000,Name:1000,Partition:1000,TimeUsed:1000,SubmitTime:1000,StartTime:1000,EndTime:1000,State:1000,ArrayJobID:1000,ArrayTaskID:1000,NodeList:1000,Reason:1000",
            ]
        ).decode("utf-8")
        # Split into lines and parse into jobs. Note quirk that if a job has no node list, the node list column is missing.
        for line in queue_info.split("\n"):
            if line:
                job_info = line.split()
                # Check that the line is the correct length
                if len(job_info) == 12:
                    # We have both nodelist and reason, so remove the reason and display only nodelist.
                    job_info.pop(11)
                if len(job_info) > 12:
                    # Maybe we have the long message "Nodes required for job are DOWN..."
                    # We want to remove the reason and replace with req. nodes not avail.
                    job_info = job_info[:10]
                    job_info.append("Nodes N. Avail.")
                if len(job_info) != 11:
                    breakpoint()
                    raise SlurmQueueReadError(
                        "Error reading slurm queue. Please check your for any irregularities in squeue output."
                    )
                self.jobs.append(SlurmJob(*job_info))

        # Filter jobs
        self.jobs = self.filter_jobs(self.jobs, job_filter_attribute, job_filter_regex)

    def filter_jobs(self, jobs: List[SlurmJob], attribute: str = "", regex: str = ""):
        """Filter jobs by attribute and regex."""
        filtered_jobs = []
        # If empty attribute or regex, return all jobs
        if not attribute or not regex:
            return jobs
        # Filter jobs
        for job in jobs:
            attr = getattr(job, attribute)
            # Use regex to filter
            if attr and re.search(regex, attr):
                filtered_jobs.append(job)
        return filtered_jobs

    def kill_job(self, job: SlurmJob):
        """Kill a job."""
        # Only killing if job id is a number allows us to use the fake job
        # to display the column names
        if job.job_id.isdigit():
            subprocess.run(["scancel", job.job_id])

    def hold_job(self, job: SlurmJob):
        """Hold a job."""
        if job.job_id.isdigit():
            subprocess.run(["scontrol", "hold", job.job_id])

    def release_job(self, job: SlurmJob):
        """Release a job."""
        if job.job_id.isdigit():
            subprocess.run(["scontrol", "release", job.job_id])

    def __getitem__(self, index):
        return self.jobs[index]

    def __len__(self):
        return len(self.jobs)
