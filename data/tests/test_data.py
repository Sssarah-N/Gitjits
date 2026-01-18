from unittest.mock import patch, MagicMock
from bson import ObjectId

import pytest

import data.db_connect as dbc


@pytest.fixture(autouse=True)
def reset_client():
    """Reset client before each test to ensure test isolation."""
    dbc.client = None
    yield
    dbc.client = None


def test_convert_mongo_id():
    """Test that convert_mongo_id converts ObjectId to string."""
    doc = {'_id': ObjectId(), 'name': 'test'}
    dbc.convert_mongo_id(doc)
    assert isinstance(doc['_id'], str)
    assert doc['name'] == 'test'


@patch('data.db_connect.pm.MongoClient')
def test_connect_db_local(mock_mongo_client):
    """Test connecting to local MongoDB."""
    mock_client = MagicMock()
    mock_client.admin.command.return_value = True
    mock_mongo_client.return_value = mock_client

    with patch.dict('os.environ', {'CLOUD': '0'}):
        result = dbc.connect_db()

    assert result == mock_client
    assert dbc.client == mock_client


def test_close_db():
    """Test that close_db closes and resets the client."""
    mock_client = MagicMock()
    dbc.client = mock_client

    dbc.close_db()

    mock_client.close.assert_called_once()
    assert dbc.client is None


@patch('data.db_connect.connect_db')
def test_create(mock_connect):
    """Test creating a document."""
    mock_client = MagicMock()
    mock_collection = MagicMock()
    mock_result = MagicMock()
    mock_result.inserted_id = ObjectId()
    mock_collection.insert_one.return_value = mock_result
    mock_db = mock_client.__getitem__.return_value
    mock_db.__getitem__.return_value = mock_collection
    dbc.client = mock_client

    doc = {'name': 'test'}
    result = dbc.create('test_collection', doc)

    assert isinstance(result, str)
    mock_collection.insert_one.assert_called_once_with(doc)


@patch('data.db_connect.connect_db')
def test_read_one(mock_connect):
    """Test reading one document."""
    mock_client = MagicMock()
    mock_collection = MagicMock()
    test_doc = {'_id': ObjectId(), 'name': 'test'}
    mock_collection.find.return_value = [test_doc]
    mock_db = mock_client.__getitem__.return_value
    mock_db.__getitem__.return_value = mock_collection
    dbc.client = mock_client

    result = dbc.read_one('test_collection', {'name': 'test'})

    assert result is not None
    assert isinstance(result['_id'], str)
    assert result['name'] == 'test'


@patch('data.db_connect.connect_db')
def test_read(mock_connect):
    """Test reading all documents from collection."""
    mock_client = MagicMock()
    mock_collection = MagicMock()
    test_docs = [
        {'_id': ObjectId(), 'name': 'test1'},
        {'_id': ObjectId(), 'name': 'test2'}
    ]
    mock_collection.find.return_value = test_docs
    mock_db = mock_client.__getitem__.return_value
    mock_db.__getitem__.return_value = mock_collection
    dbc.client = mock_client

    result = dbc.read('test_collection', no_id=True)

    assert len(result) == 2
    assert '_id' not in result[0]
    assert result[0]['name'] == 'test1'


@patch('data.db_connect.connect_db')
def test_delete(mock_connect):
    """Test deleting a document."""
    mock_client = MagicMock()
    mock_collection = MagicMock()
    mock_result = MagicMock()
    mock_result.deleted_count = 1
    mock_collection.delete_one.return_value = mock_result
    mock_db = mock_client.__getitem__.return_value
    mock_db.__getitem__.return_value = mock_collection
    dbc.client = mock_client

    result = dbc.delete('test_collection', {'name': 'test'})

    assert result == 1
    mock_collection.delete_one.assert_called_once_with({'name': 'test'})


@patch('data.db_connect.connect_db',
       side_effect=ConnectionError("Cannot connect"))
def test_read_connection_error(mock_connect):
    """Test that read raises ConnectionError when DB unavailable."""
    dbc.client = None
    with pytest.raises(ConnectionError):
        dbc.read('test_collection')
