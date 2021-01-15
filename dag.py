# To be used for airflow
from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator

import sys
repo_dir = "/mnt/sonar_miner"
sys.path.append(repo_dir)

from sonar_src import fetch_sonar_data
from merge_stage_archive import main

from datetime import datetime, timedelta, date

default_args = {
    'owner': 'hung',
    'depends_on_past': False,
    'start_date': datetime(2020,10,3),
    'email': ['hung.nguyen@tuni.fi'],
    'email_on_failure': True,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG('sonar_miner', default_args = default_args, schedule_interval = '0 0 * * *')

t1 = PythonOperator(
    task_id = 'fetch_sonarqube_data',
    provide_context=False,
    python_callable= fetch_sonar_data,
    op_args=[f'{repo_dir}/sonar_data'],
    dag = dag
)


t2 = PythonOperator(
    task_id = "merge_stage_archive",
    provide_context=False,
    python_callable= main,
    op_args=[f"{repo_dir}/sonar_data"],
    dag = dag
)

t1 >> t2
