from airflow.models import DagBag


def test_dag_bag_imports_without_errors():
    dag_bag = DagBag(dag_folder="dags")
    assert not dag_bag.import_errors, dag_bag.import_errors


def test_wikivoyage_ingest_dag_structure():
    dag_bag = DagBag(dag_folder="dags")
    dag = dag_bag.get_dag("wikivoyage_ingest")
    assert dag is not None
    assert set(dag.task_ids) == {
        "fetch_dump", "clean_normalize", "chunk_articles",
        "embed_batch", "upsert_pgvector",
    }
