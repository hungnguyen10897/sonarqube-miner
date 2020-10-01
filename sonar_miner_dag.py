# To be used for airflow
from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator

import sys
repo_dir = "/mnt/sonar_miner"
pra_repo_dir = "/mnt/pra"
sys.path.append(repo_dir)
sys.path.append(pra_repo_dir)

from sonarcloud_data.sonar_miner import fetch_sonar_data
from merge_stage_archive import main

from datetime import datetime, timedelta, date

default_args = {
    'owner': 'hung',
    'depends_on_past': False,
    'start_date': datetime(2020,10,1),
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
    op_args=[f'{repo_dir}/sonar_data/data'],
    dag = dag
)


t2 = PythonOperator(
    task_id = "merge_stage_archive",
    provide_context=False,
    python_callable= main,
    op_args=[f"{repo_dir}/sonar_data/data"],
    dag = dag
)

t1 >> t2
