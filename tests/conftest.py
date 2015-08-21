import pytest

import utils
import vcli.vexecute


@pytest.yield_fixture(scope="function")
def connection():
    utils.create_schema()
    connection = utils.db_connection()
    yield connection

    utils.drop_schema(connection)
    connection.close()


@pytest.fixture
def cursor(connection):
    with connection.cursor() as cur:
        return cur


@pytest.fixture
def executor(connection):
    return vcli.vexecute.VExecute(
        database=utils.VERTICA_DATABASE, user=utils.VERTICA_USER,
        host=utils.VERTICA_HOST, password=utils.VERTICA_PASSWORD, port=5433)
