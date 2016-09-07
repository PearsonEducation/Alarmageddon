"Unit Tests for HttpValidation"""
from pytest_localserver.http import WSGIServer
from alarmageddon.validations.http import HttpValidation
from alarmageddon.validations.exceptions import ValidationFailure
import pytest
import time
import requests
import json


def slow_app(environ, start_response):
    status = '200 OK'
    response_headers = [('Content-type', 'text/plain')]
    start_response(status, response_headers)
    time.sleep(4)
    return ["Slow?!\n"]


def pytest_funcarg__slowserver(request):
    """Defines the testserver funcarg"""
    server = WSGIServer(application=slow_app)
    server.start()
    request.addfinalizer(server.stop)
    return server


def test_repr():
    name = "http://thread-stats.qaprod.pearsonopenclass.com/version"
    validation = HttpValidation.get(name)
    validation.__repr__()


def test_str():
    name = "http://thread-stats.qaprod.pearsonopenclass.com/version"
    validation = HttpValidation.get(name)
    str(validation)


def test_http_name_get():
    name = "http://thread-stats.qaprod.pearsonopenclass.com/version"
    validation = HttpValidation.get(name)
    name = validation.timer_name()
    expected = "http.com.pearsonopenclass.qaprod.thread-stats.version.GET"
    assert name == expected


def test_http_name_get_query():
    name = "http://thread-stats.pearsonopenclass.com/version?foo=bar"
    validation = HttpValidation.get(name)
    name = validation.timer_name()
    expected = "http.com.pearsonopenclass.thread-stats.version.foo=bar.GET"
    assert name == expected


def test_http_name_https():
    name = "https://thread-stats.qaprod.pearsonopenclass.com/version"
    validation = HttpValidation.get(name)
    name = validation.timer_name()
    expected = "https.com.pearsonopenclass.qaprod.thread-stats.version.GET"
    assert name == expected


def test_http_name_post():
    name = "http://thread-stats.qaprod.pearsonopenclass.com/version"
    validation = HttpValidation.post(name)
    name = validation.timer_name()
    expected = "http.com.pearsonopenclass.qaprod.thread-stats.version.POST"
    assert name == expected


def test_get_json_value(httpserver):
    httpserver.serve_content(code=200,
                             headers={"content-type": "application/json"},
                             content='{"mode": "NORMAL"}')
    (HttpValidation.get(httpserver.url)
     .expect_json_property_value("mode", "NORMAL")
     .perform({}))


def test_get_json_value_greater_than(httpserver):
    httpserver.serve_content(code=200,
                             headers={"content-type": "application/json"},
                             content='{"mode": "NORMAL","numExecutors":3}')
    (HttpValidation.get(httpserver.url)
     .expect_json_property_value_greater_than("numExecutors", 2)
     .perform({}))


def test_get_array_value(httpserver):
    httpserver.serve_content(code=200,
                             headers={"content-type": "application/json"},
                             content='{"num":3,"views":[{"name": "All"},' +
                                     '{"name": "None"}]}')
    (HttpValidation.get(httpserver.url)
     .expect_json_property_value("views[0].name", "All")
     .perform({}))


def test_expected_content_type(httpserver):
    httpserver.serve_content(code=200,
                             headers={"content-type": "application/json"},
                             content='{"mode": "NORMAL"}')
    (HttpValidation.get(httpserver.url)
     .expect_json_property_value("mode", "NORMAL")
     .expect_content_type("application/json")
     .perform({}))


def test_expected_content_type_correctly_fails(httpserver):
    httpserver.serve_content(code=200,
                             headers={"content-type": "plain/text"},
                             content='{"mode": "NORMAL"}')
    with pytest.raises(ValidationFailure):
        (HttpValidation.get(httpserver.url)
         .expect_json_property_value("mode", "NORMAL")
         .expect_content_type("application/json")
         .perform({}))


def test_expected_code_default_to_200(httpserver):
    httpserver.serve_content(code=200,
                             headers={"content-type": "application/json"},
                             content='{}')
    (HttpValidation.get(httpserver.url)
     .perform({}))


def test_expected_code_default_correctly_fails(httpserver):
    httpserver.serve_content(code=400,
                             headers={"content-type": "application/json"},
                             content='{}')
    with pytest.raises(ValidationFailure):
        (HttpValidation.get(httpserver.url)
         .perform({}))


def test_expected_code_correct_on_set(httpserver):
    httpserver.serve_content(code=200,
                             headers={"content-type": "application/json"},
                             content='{}')
    (HttpValidation.get(httpserver.url)
     .expect_status_codes(set(range(200, 300)))
     .perform({}))


def test_expected_code(httpserver):
    httpserver.serve_content(code=300,
                             headers={"content-type": "application/json"},
                             content='{}')
    (HttpValidation.get(httpserver.url)
     .expect_status_codes([300])
     .perform({}))


def test_expected_code_correctly_fails(httpserver):
    httpserver.serve_content(code=401,
                             headers={"content-type": "application/json"},
                             content='{}')
    with pytest.raises(ValidationFailure):
        (HttpValidation.get(httpserver.url)
         .expect_status_codes([200])
         .perform({}))


def test_expected_text(httpserver):
    httpserver.serve_content(code=200,
                             headers={"header": "exists"},
                             content="Here is some text!")
    (HttpValidation.get(httpserver.url)
     .expect_contains_text("is some")
     .perform({}))


def test_expected_text_correctly_fails(httpserver):
    httpserver.serve_content(code=200,
                             headers={"header": "exists"},
                             content="Here is some text!")
    with pytest.raises(ValidationFailure):
        (HttpValidation.get(httpserver.url)
         .expect_contains_text("words")
         .perform({}))


def test_expected_header(httpserver):
    httpserver.serve_content(code=200,
                             headers={"header": "exists"},
                             content="this")
    (HttpValidation.get(httpserver.url)
     .expect_header("header", "exists")
     .perform({}))


def test_expected_header_bad_key(httpserver):
    httpserver.serve_content(code=200,
                             headers={"wrong": "exists"},
                             content="this")
    with pytest.raises(ValidationFailure):
        (HttpValidation.get(httpserver.url)
         .expect_header("header", "exists")
         .perform({}))


def test_expected_header_bad_value(httpserver):
    httpserver.serve_content(code=200,
                             headers={"header": "nope"},
                             content="this")
    with pytest.raises(ValidationFailure):
        (HttpValidation.get(httpserver.url)
         .expect_header("header", "exists")
         .perform({}))


def test_get_json_value_fails(httpserver):
    httpserver.serve_content(code=200,
                             headers={"content-type": "application/json"},
                             content='{"mode": "ABNORMAL"}')
    with pytest.raises(ValidationFailure):
        (HttpValidation.get(httpserver.url)
         .expect_json_property_value("mode", "NORMAL")
         .perform({}))


def test_get_json_key_fails(httpserver):
    httpserver.serve_content(code=200,
                             headers={"content-type": "application/json"},
                             content='{"key": "NORMAL"}')
    with pytest.raises(ValidationFailure):
        (HttpValidation.get(httpserver.url)
         .expect_json_property_value("mode", "NORMAL")
         .perform({}))


def test_properly_records_elapsed_time(slowserver):
    val = HttpValidation.get(slowserver.url)
    val.perform({})
    #should be ~4, but add some buffer since sleep doesn't actually
    #guarantee anything about how long it will sleep
    assert 3.8 < val._elapsed_time < 4.2


def test_properly_times_out(slowserver):
    val = HttpValidation.get(slowserver.url, timeout=3)
    with pytest.raises(requests.exceptions.Timeout):
        val.perform({})


def test_properly_records_elapsed_time_on_timeout(slowserver):
    val = HttpValidation.get(slowserver.url, timeout=3)
    try:
        val.perform({})
    except requests.exceptions.Timeout:
        pass
    #specifically in this case the elapsed time should be the timeout
    assert val._elapsed_time == 3


def test_duplicate_with_hosts():
    validation = HttpValidation.get("hostname:8080")
    new = validation.duplicate_with_hosts(["firstname", "secondname"])

    first = new[0]
    assert first._data == validation._data
    assert first._method == validation._method
    assert first._headers == validation._headers
    assert first._expectations == validation._expectations
    assert first._retries == validation._retries
    assert first._ignore_ssl_cert_errors == validation._ignore_ssl_cert_errors
    assert first._auth == validation._auth

    names = [v._url for v in new]
    assert "firstname" in names[0]
    assert "secondname" in names[1]
    assert len(names) == 2

# Test submitted by Curtis Allen (https://github.com/curtisallen).
# Thanks Curtis!
#
# Bug: We found the value of the failed property which was zero and
# tested it using 'if not actual_value' which evaluated to False.
def test_get_json_value_less_than_zero(httpserver):
    httpserver.serve_content(code=200,
                             headers={"content-type": "application/json"},
                             content='{"mode": "NORMAL","failed":0}')
    (HttpValidation.get(httpserver.url)
     .expect_json_property_value_less_than('failed', 2)
     .perform({}))


def test_nested_json_value(httpserver):
    httpserver.serve_content(
        code=200,
        headers={"content-type": "application/json"},
        content=json.dumps({
            "took" : 270,
            "timed_out" : False,
            "_shards" : {
                "total" : 576,
                "successful" : 576,
                "failed" : 0
                },
                "hits" : {
                    "total" : 0,
                    "max_score" : 0.0,
                    "hits" : [ ]
                    }
            })
        )
    (HttpValidation.get(httpserver.url)
     .expect_json_property_value('hits.total', 0)
     .perform({}))

def test_nested_json_value_wrong_type(httpserver):
    httpserver.serve_content(
        code=200,
        headers={"content-type": "application/json"},
        content=json.dumps({
            "took" : 270,
            "timed_out" : False,
            "_shards" : {
                "total" : 576,
                "successful" : 576,
                "failed" : 0
                },
                "hits" : {
                    "total" : 0,
                    "max_score" : 0.0,
                    "hits" : [ ]
                    }
            })
        )
    with pytest.raises(ValidationFailure):
        (HttpValidation.get(httpserver.url)
        .expect_json_property_value('hits.total', '0')
        .perform({}))
