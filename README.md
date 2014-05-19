# tinyquery
tinyquery is a partial implementation of the BigQuery API that runs completely
in-memory in Python code. If you have Python code that uses the BigQuery API,
you may be able to use tinyquery to make your automated tests orders of
magnitude faster, more reliable, and less annoying to run.

## Motivation
[BigQuery](https://developers.google.com/bigquery/) is a Google service that
lets you import giant data sets and run arbitrary SQL queries over them. The
most common use case is to allow people to dig into their data manually using
SQL, but BigQuery also lets you build complex data pipelines entirely in SQL,
which makes them much more maintainable and debuggable.

One of the biggest challenges when writing a data pipeline on top of BigQuery
is writing high-quality automated tests. Normally, you're left with a few
less-than-perfect options:

* Skip automated testing and rely only on manual testing.
* Mock out the BigQuery service. This lets you test some basic things, but
won't give you confidence in your system if you have a nontrivial amount of
SQL.
* Run tests against some other SQL implementation that can be run locally.
Since every dialect of SQL is different (and with BigQuery having a
dramatically different architecture than a typical relational database), this
would likely cause more trouble than it's worth.
* Run tests against the real BigQuery service. This is probably the best
option, but has a few problems:
    * The tests can get very slow as the code gets more complex, since they
    will involve lots of network I/O over the internet and BigQuery operations
    tend to have highly-variable response times anyway.
    * Anyone running your test needs to have the right credentials to access
    BigQuery.
    * Running the test requires an internet connection.
    * If you don't take additional measures, two people running the test at the
    same time could trample each other's test state and cause confusing test
    failures.

tinyquery lets you write a test against the real BigQuery API, then swap out
BigQuery for a fake implementation for fast iteration. For example, tinyquery
was used to dramatically improve a test at Khan Academy that ran a large data
pipeline three times in different conditions. Originally, the test took about 8
minutes (and at its worst point took about an hour to run) and required some
manual steps. After modifying the test to use tinyquery, the test now takes 2
seconds to run and is suitable for inclusion in the standard test suite that
anyone can run.

## How to use
tinyquery is a drop-in replacement as long as you're accessing the
[BigQuery API](https://developers.google.com/bigquery/docs/developers_guide)
using the [Python client library](https://developers.google.com/api-client-library/python/).

Here's how you might set things up:

    from tinyquery import tinyquery
    from tinyquery import api_client
    tq_service = tinyquery.TinyQuery()
    tq_api_client = api_client.TinyQueryApiClient(tq_service)

The `tq_service` instance gives you direct Python access to various tinyquery
operations. The `tq_api_client` instance is an API wrapper that you can
patch/inject into your production code as a replacement for the return value of
`apiclient.discovery.build()`.

If your code catches the `apiclient.errors.HttpError` exception, you may also
want to patch `tinyquery.api_client.FakeHttpError` with that class.

## Features

* Almost all of the core SQL language: SELECT, FROM, WHERE, GROUP BY, JOIN
(including LEFT OUTER JOIN and CROSS JOIN), LIMIT, subqueries.
* Many of the common functions and operators. See runtime.py for a list.
* Importing from CSV.
* API wrappers for creating, getting, and deleting tables, and for creating and
managing query and copy jobs and getting query results.

## What's missing?
Quite a bit, currently, although many of these things shouldn't be *that* hard
to implement:

* ORDER BY.
* HAVING.
* JOIN on more than two tables.
* Repeated columns and record columns, and all of the features that go along
with them:
    * FLATTEN
    * WITHIN and scoped aggregation
    * POSITION and NEST
* Window functions and OVER/PARTITION BY.
* Native timestamps and timestamp functions.
* Import from JSON.
* Various operators and functions.
* The existing functions probably don't do type checking or null handling in
quite the same way that BigQuery does.
* Lots of API operations are unsupported. The ones that are supported are
missing various return fields from the API.
* There are some edge cases in the core language where BigQuery and tinyquery
differ, most of which involve fully-qualified column names (e.g.
`table_alias.column` being allowed in tinyquery but not BigQuery or vice
versa).
