import pytest
from datetime import datetime, timezone

from app.routes import jobs as jobs_module


class _FakeSupabaseResponse:
    def __init__(self, data=None, error=None):
        self.data = data
        self.error = error


class _FakeSupabaseInsert:
    def __init__(self, response):
        self._response = response
        self.last_record = None

    def insert(self, record):
        self.last_record = record
        return self

    def execute(self):
        return self._response


class _FakeRangeQuery:
    def __init__(self, data=None, error=None):
        self.data = data or []
        self.error = error
        self.filters: list[tuple[str, str, object]] = []
        self.order_args: tuple | None = None
        self.range_args: tuple[int, int] | None = None

    def select(self, *_args):
        return self

    def order(self, *args, **kwargs):
        self.order_args = (args, kwargs)
        return self

    def eq(self, column: str, value: object):
        self.filters.append(("eq", column, value))
        return self

    def contains(self, column: str, value: object):
        self.filters.append(("contains", column, value))
        return self

    def range(self, start: int, end: int):
        self.range_args = (start, end)
        return self

    def execute(self):
        return _FakeSupabaseResponse(data=list(self.data), error=self.error)


class _FakeSupabaseClient:
    def __init__(self, table_impl):
        self._table_impl = table_impl
        self.table_name = None

    def table(self, name: str):
        self.table_name = name
        return self._table_impl


@pytest.mark.asyncio
async def test_create_job_success(monkeypatch):
    response_data = {"id": "job-uuid", "status": "posted"}
    response = _FakeSupabaseResponse(data=[response_data])
    table_impl = _FakeSupabaseInsert(response)
    client = _FakeSupabaseClient(table_impl)

    monkeypatch.setattr(jobs_module, "get_supabase_client", lambda: client)

    payload = jobs_module.JobCreate(
        title="Test Job",
        description="Do something",
        capabilities=["code"],
        payment_token="0xUSDC",
        escrow_amount="100",
        deadline=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    result = await jobs_module.create_job(payload, poster_address="0xposter")

    assert result == response_data
    assert client.table_name == "jobs"

    record = table_impl.last_record
    assert record["poster_address"] == "0xposter"
    assert record["title"] == "Test Job"
    assert record["description"] == "Do something"
    assert record["required_capabilities"] == ["code"]
    assert record["payment_token"] == "0xUSDC"
    assert record["escrow_amount"] == "100"
    assert record["deadline"] == payload.deadline
    assert record["status"] == "posted"
    assert record["job_spec_hash"] == jobs_module._compute_job_spec_hash("Do something")


@pytest.mark.asyncio
async def test_list_jobs_filters_and_pagination(monkeypatch):
    data = [{"id": "job-1"}, {"id": "job-2"}, {"id": "job-3"}]
    query = _FakeRangeQuery(data=data)
    client = _FakeSupabaseClient(query)

    monkeypatch.setattr(jobs_module, "get_supabase_client", lambda: client)

    result = await jobs_module.list_jobs(
        status="posted",
        capabilities=["code"],
        sort="deadline",
        limit=1,
        cursor="1",
    )

    assert result["data"] == data[:1]
    assert result["cursor"] == "2"

    assert query.range_args == (1, 2)
    assert query.order_args is not None
    assert ("eq", "status", "posted") in query.filters
    assert ("contains", "required_capabilities", ["code"]) in query.filters
