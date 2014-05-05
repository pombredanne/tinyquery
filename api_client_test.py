import unittest

import api_client
import tinyquery


class ApiClientTest(unittest.TestCase):
    def setUp(self):
        self.tinyquery = tinyquery.TinyQuery()
        self.tq_service = api_client.TinyQueryApiClient(self.tinyquery)

    @staticmethod
    def table_ref(table_name):
        return {
            'projectId': 'test_project',
            'datasetId': 'test_dataset',
            'tableId': table_name,
        }

    def insert_simple_table(self):
        self.tq_service.tables().insert(
            projectId='test_project',
            datasetId='test_dataset',
            body={
                'tableReference': self.table_ref('test_table'),
                'schema': {
                    'fields': [
                        {'name': 'foo', 'type': 'INTEGER'},
                        {'name': 'bar', 'type': 'BOOLEAN'},
                    ]
                }
            }).execute()

    def test_table_management(self):
        self.insert_simple_table()
        table_info = self.tq_service.tables().get(
            projectId='test_project', datasetId='test_dataset',
            tableId='test_table').execute()
        self.assertEqual(
            {'name': 'bar', 'type': 'BOOLEAN', 'mode': 'NULLABLE'},
            table_info['schema']['fields'][1])

        self.tq_service.tables().delete(
            projectId='test_project', datasetId='test_dataset',
            tableId='test_table').execute()

        try:
            self.tq_service.tables().get(
                projectId='test_project', datasetId='test_dataset',
                tableId='test_table').execute()
            self.fail('Expected exception to be raised.')
        except api_client.FakeHttpError as e:
            self.assertTrue('404' in e.content)

        try:
            self.tq_service.tables().delete(
                projectId='test_project', datasetId='test_dataset',
                tableId='test_table').execute()
            self.fail('Expected exception to be raised.')
        except api_client.FakeHttpError as e:
            self.assertTrue('404' in e.content)

    def test_simple_query(self):
        job_info = self.tq_service.jobs().insert(
            projectId='test_project',
            body={
                'projectId': 'test_project',
                'configuration': {
                    'query': {
                        'query': 'SELECT 7 as foo',
                    }
                }
            }
        ).execute()
        query_result = self.tq_service.jobs().getQueryResults(
            projectId='test_project', jobId=job_info['jobReference']['jobId']
        ).execute()
        self.assertEqual('7', query_result['rows'][0]['f'][0]['v'])

    def test_table_copy(self):
        self.tq_service.jobs().insert(
            projectId='test_project',
            body={
                'projectId': 'test_project',
                'configuration': {
                    'query': {
                        'query': 'SELECT 7 as foo',
                        'destinationTable': self.table_ref('table1')
                    },
                },
            }
        ).execute()

        for _ in xrange(5):
            self.tq_service.jobs().insert(
                projectId='test_project',
                body={
                    'projectId': 'test_project',
                    'configuration': {
                        'copy': {
                            'sourceTable': self.table_ref('table1'),
                            'destinationTable': self.table_ref('table2'),
                            'createDisposition': 'CREATE_IF_NEEDED',
                            'writeDisposition': 'WRITE_APPEND',
                        }
                    }
                }
            ).execute()

        query_job_info = self.tq_service.jobs().insert(
            projectId='test_project',
            body={
                'projectId': 'test_project',
                'configuration': {
                    'query': {
                        'query': 'SELECT foo FROM test_dataset.table2',
                    }
                }
            }
        ).execute()
        query_result = self.tq_service.jobs().getQueryResults(
            projectId='test_project',
            jobId=query_job_info['jobReference']['jobId']
        ).execute()
        self.assertEqual(5, len(query_result['rows']))