import pytest
from alarmageddon.validations.validation import\
    Priority, Validation, GroupValidation
from alarmageddon.publishing import publisher
from alarmageddon.publishing import pagerduty
from alarmageddon.validations.exceptions import EnrichmentFailure


thresholds = [0, 3, 5]


@pytest.fixture(params=[True, False])
def bools(request):
    return request.param


@pytest.fixture(params=thresholds)
def lows(request):
    return request.param


@pytest.fixture(params=thresholds)
def normals(request):
    return request.param


@pytest.fixture(params=thresholds)
def criticals(request):
    return request.param


@pytest.fixture(params=range(5))
def failures(request):
    return request.param


@pytest.fixture(params=[1, 2])
def failure_lows(request):
    return request.param


def test_priority_string():
    assert Priority.string(Priority.LOW) == "low"
    assert Priority.string(Priority.NORMAL) == "normal"
    assert Priority.string(Priority.CRITICAL) == "critical"
    assert "unknown" in Priority.string(-1)
    assert "unknown" in Priority.string("low")


def test_validation_str():
    v = Validation("name")
    v.__str__()


def test_repr():
    v = Validation("name")
    v.__repr__()


def test_group_validation_correct_thresholds(lows, normals, criticals):
    v = GroupValidation("name", "group", low_threshold=lows,
                        normal_threshold=normals, critical_threshold=criticals)
    assert v.low_threshold <= v.normal_threshold <= v.critical_threshold


def test_group_validation_handles_failures_correctly(failures, failure_lows):
    v = GroupValidation("name", "group", low_threshold=failure_lows,
                        normal_threshold=2, critical_threshold=3)
    v._set_priority(failures)
    if failures > lows:
        assert v.priority >= Priority.LOW
    if failures > normals:
        assert v.priority >= Priority.NORMAL
    if failures > criticals:
        assert v.priority >= Priority.CRITICAL


def test_simple_enrichment_case():
    values = {1: 2, "a": "b"}
    valid = Validation("low", Priority.LOW)
    pub = publisher.Publisher(priority_threshold=Priority.CRITICAL)
    valid.enrich(pub, values)
    data = valid.get_enriched(pub)
    assert data == values


def test_simple_enrichment_forced_namespace():
    values = {1: 2, "a": "b"}
    valid = Validation("low", Priority.LOW)
    pub = publisher.Publisher(priority_threshold=Priority.CRITICAL)
    valid.enrich(pub, values, force_namespace=True)
    data = valid.get_enriched(pub)
    assert data == values


def test_empty_enrichment_case():
    values = {}
    valid = Validation("low", Priority.LOW)
    pub = publisher.Publisher(priority_threshold=Priority.CRITICAL)
    valid.enrich(pub, values)
    data = valid.get_enriched(pub)
    assert data == values


def test_enrichment_fails_on_duplication():
    values = {1: 2, "a": "b"}
    valid = Validation("low", Priority.LOW)
    pub = publisher.Publisher(priority_threshold=Priority.CRITICAL)
    valid.enrich(pub, values)
    with pytest.raises(EnrichmentFailure):
        valid.enrich(pub, values)


def test_enrichment_fails_on_duplication_different_data():
    values = {1: 2, "a": "b"}
    valid = Validation("low", Priority.LOW)
    pub = publisher.Publisher(priority_threshold=Priority.CRITICAL)
    valid.enrich(pub, values)
    with pytest.raises(EnrichmentFailure):
        valid.enrich(pub, {"different": "values"})


def test_two_enrichments_correctness_independent_of_force(bools):
    pub_values = {1: 2, "a": "b"}
    page_values = {1: 5, "a": "3", "what": "who"}
    valid = Validation("low", Priority.LOW)
    pub = publisher.Publisher(priority_threshold=Priority.CRITICAL)
    page = pagerduty.PagerDutyPublisher("url", "token")
    valid.enrich(pub, pub_values, force_namespace=bools)
    valid.enrich(page, page_values, force_namespace=bools)
    pub_data = valid.get_enriched(pub)
    page_data = valid.get_enriched(page)
    for item in pub_values.items():
        assert item in pub_data.items()
    for item in page_values.items():
        assert item in page_data.items()


def test_two_enrichments_correctness_independent_of_force_reverse(bools):
    pub_values = {1: 2, "a": "b"}
    page_values = {1: 5, "a": "3", "what": "who"}
    valid = Validation("low", Priority.LOW)
    pub = publisher.Publisher(priority_threshold=Priority.CRITICAL)
    page = pagerduty.PagerDutyPublisher("url", "token")
    valid.enrich(page, page_values, force_namespace=bools)
    valid.enrich(pub, pub_values, force_namespace=bools)
    pub_data = valid.get_enriched(pub)
    page_data = valid.get_enriched(page)
    for item in pub_values.items():
        assert item in pub_data.items()
    for item in page_values.items():
        assert item in page_data.items()


def test_get_empty_enrichment():
    valid = Validation("low", Priority.LOW)
    pub = publisher.Publisher(priority_threshold=Priority.CRITICAL)
    assert valid.get_enriched(pub) == {}


def test_get_wrong_enrichment():
    pub_values = {1: 2, "a": "b"}
    valid = Validation("low", Priority.LOW)
    pub = publisher.Publisher(priority_threshold=Priority.CRITICAL)
    page = pagerduty.PagerDutyPublisher("url", "token")
    valid.enrich(pub, pub_values)
    assert valid.get_enriched(page) == pub_values


def test_get_wrong_enrichment_forced_namespace():
    pub_values = {1: 2, "a": "b"}
    valid = Validation("low", Priority.LOW)
    pub = publisher.Publisher(priority_threshold=Priority.CRITICAL)
    page = pagerduty.PagerDutyPublisher("url", "token")
    valid.enrich(pub, pub_values, force_namespace=True)
    assert valid.get_enriched(page) == {}


def test_get_enrichment_forced_namespace():
    pub_values = {1: 2, "a": "b"}
    page_values = {1: 5, "what": "who"}
    valid = Validation("low", Priority.LOW)
    pub = publisher.Publisher(priority_threshold=Priority.CRITICAL)
    page = pagerduty.PagerDutyPublisher("url", "token")
    valid.enrich(pub, pub_values, force_namespace=True)
    valid.enrich(page, page_values, force_namespace=True)
    assert valid.get_enriched(page, force_namespace=True) == {1: 5, "what": "who"}
