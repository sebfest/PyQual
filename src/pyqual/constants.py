BASE_URL = 'https://{0}.qualtrics.com/API/v3/'
ENDPOINTS = {
    'filters': '/surveys/{0}/filters',
    'export': 'surveys/{0}/export-responses/',
    'surveys': 'surveys',
    'get_survey': 'surveys/{0}',
    'directories': 'directories',
}
DATA_CENTERS = [
    'fra1',
    'ca1',
    'iad1',
    'sjc1',
    'syd1',
    'gov1'
]
FILE_EXTENSION = [
    'csv',
    'tsv',
    'json',
    'xml',
    'ndjson',
    'json',
    'spss'
]
PAGE_SIZE = 100
