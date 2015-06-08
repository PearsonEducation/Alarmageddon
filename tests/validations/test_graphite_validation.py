import pytest
from alarmageddon.validations.exceptions import ValidationFailure
from alarmageddon.validations.graphite import GraphiteContext,\
    GraphiteValidation


def establishServer(httpserver, counts):
    content = 'ParticipationIndex.404-Not-Found-count.count,1397748470,1397752070,10|{}'.format(counts)

    httpserver.serve_content(code=200,
                             headers={"content-type": "text/plain"},
                             content=content)


def test_repr(httpserver):
    establishServer(httpserver, "None,10,None,30,45,None,None")
    ctx = GraphiteContext(httpserver.url)
    v = GraphiteValidation(ctx, "ParticipationIndex Internal Server Errors",
                       "ParticipationIndex.404-Not-Found-count.count")
    v.__repr__()


def test_detect_max_exceeded(httpserver):
    establishServer(httpserver, "None,10,None,30,45,None,None")
    ctx = GraphiteContext(httpserver.url)
    with pytest.raises(ValidationFailure):
        GraphiteValidation(ctx, "ParticipationIndex Internal Server Errors",
                           "ParticipationIndex.404-Not-Found-count.count") \
            .expect_less_than(40) \
            .perform({})
        assert False


def test_detect_min_exceeded(httpserver):
    establishServer(httpserver, "None,10,1,30,45,None,None")
    ctx = GraphiteContext(httpserver.url)
    with pytest.raises(ValidationFailure):
        GraphiteValidation(ctx, "ParticipationIndex Internal Server Errors",
                           "ParticipationIndex.404-Not-Found-count.count") \
            .expect_greater_than(2) \
            .perform({})


def test_detect_max_not_exceeded(httpserver):
    establishServer(httpserver, "None,10,None,30,45,None,None")
    ctx = GraphiteContext(httpserver.url)
    GraphiteValidation(ctx, "ParticipationIndex Internal Server Errors",
                       "ParticipationIndex.404-Not-Found-count.count") \
        .expect_less_than(1000) \
        .perform({})


def test_detect_average_not_exceeded(httpserver):
    establishServer(httpserver, "None,10,None,30,45,None,None")
    ctx = GraphiteContext(httpserver.url)
    GraphiteValidation(ctx, "ParticipationIndex Internal Server Errors",
                       "ParticipationIndex.404-Not-Found-count.count") \
        .expect_average_less_than(500) \
        .perform({})


def test__min_not_exceeded(httpserver):
    establishServer(httpserver, "3,10,3,30,45,3,3")
    ctx = GraphiteContext(httpserver.url)
    GraphiteValidation(ctx, "ParticipationIndex Internal Server Errors",
                       "ParticipationIndex.404-Not-Found-count.count") \
        .expect_greater_than(1) \
        .perform({})


def test_within_range(httpserver):
    establishServer(httpserver, "3,10,3,30,45,3,3")
    ctx = GraphiteContext(httpserver.url)
    GraphiteValidation(ctx, "ParticipationIndex Internal Server Errors",
                       "ParticipationIndex.404-Not-Found-count.count") \
        .expect_in_range(2, 1000) \
        .perform({})


def test_out_of_range_high(httpserver):
    establishServer(httpserver, "3,10,3,30,45,3,3")
    ctx = GraphiteContext(httpserver.url)
    with pytest.raises(ValidationFailure):
        GraphiteValidation(ctx, "ParticipationIndex Internal Server Errors",
                           "ParticipationIndex.404-Not-Found-count.count") \
            .expect_in_range(2, 20) \
            .perform({})


def test_out_of_range_low(httpserver):
    establishServer(httpserver, "3,10,3,30,45,3,3")
    ctx = GraphiteContext(httpserver.url)
    with pytest.raises(ValidationFailure):
        GraphiteValidation(ctx, "ParticipationIndex Internal Server Errors",
                           "ParticipationIndex.404-Not-Found-count.count") \
            .expect_in_range(5, 400) \
            .perform({})


def test_average_in_range(httpserver):
    establishServer(httpserver, "3,10,3,30,45,3,3")
    ctx = GraphiteContext(httpserver.url)
    GraphiteValidation(ctx, "ParticipationIndex Internal Server Errors",
                       "ParticipationIndex.404-Not-Found-count.count") \
        .expect_average_in_range(0, 500) \
        .perform({})
