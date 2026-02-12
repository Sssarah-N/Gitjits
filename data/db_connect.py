"""
All interaction with MongoDB should be through this file!
We may be required to use a new database at any point.
"""
import os
from functools import wraps
import pymongo as pm
import pymongo.errors
import certifi

LOCAL = "0"
CLOUD = "1"

GEO_DB = 'geo2025DB'

client = None

MONGO_ID = '_id'

# parameter names of mongo client settings
SERVER_API_PARAM = 'server_api'
CONN_TIMEOUT = 'connectTimeoutMS'
SOCK_TIMEOUT = 'socketTimeoutMS'
CONNECT = 'connect'
MAX_POOL_SIZE = 'maxPoolSize'

# Recommended Python Anywhere settings.
PA_MONGO = os.getenv('PA_MONGO', True)
PA_SETTINGS = {
    CONN_TIMEOUT: os.getenv('MONGO_CONN_TIMEOUT', 30000),
    SOCK_TIMEOUT: os.getenv('MONGO_SOCK_TIMEOUT', None),
    CONNECT: os.getenv('MONGO_CONNECT', False),
    MAX_POOL_SIZE: os.getenv('MONGO_MAX_POOL_SIZE', 1),
}


def needs_db(fn, *args, **kwargs):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # global client
        if not client:
            connect_db()
        return fn(*args, **kwargs)
    return wrapper


def connect_db():
    """
    This provides a uniform way to connect to the DB across all uses.
    Returns a mongo client object... maybe we shouldn't?
    Also set global client variable.
    We should probably either return a client OR set a
    client global.
    """
    global client
    if client is None:  # not connected yet!
        print('Setting client because it is None.')
        if os.environ.get('CLOUD', LOCAL) == CLOUD:
            password = os.environ.get('MONGO_PASSWD')
            if not password:
                raise ValueError('You must set your password '
                                 + 'to use Mongo in the cloud.')
            print('Connecting to Mongo in the cloud.')
            try:
                client = pm.MongoClient(f'mongodb+srv://Gitjits:{password}'
                                        + '@gitjits.zzxtdpz.mongodb.net/'
                                        + '?appName=Gitjits',
                                        serverSelectionTimeoutMS=5000,
                                        tlsCAFile=certifi.where(),
                                        **PA_SETTINGS
                                        )
                # Test the connection
                client.admin.command('ping')
            except (pymongo.errors.ServerSelectionTimeoutError,
                    pymongo.errors.ConfigurationError,
                    pymongo.errors.OperationFailure) as e:
                raise ConnectionError(
                    f'Failed to connect to MongoDB: {str(e)}'
                ) from e
        else:
            print("Connecting to Mongo locally.")
            try:
                client = pm.MongoClient(serverSelectionTimeoutMS=5000)
                # Test the connection
                client.admin.command('ping')
            except (pymongo.errors.ServerSelectionTimeoutError,
                    pymongo.errors.ConfigurationError) as e:
                raise ConnectionError(
                    f'Failed to connect to local MongoDB: {str(e)}'
                ) from e
    return client


def convert_mongo_id(doc: dict):
    if MONGO_ID in doc:
        # Convert mongo ID to a string so it works as JSON
        doc[MONGO_ID] = str(doc[MONGO_ID])
    # Remove duplicate 'id' field if it exists (legacy data cleanup)
    if 'id' in doc and MONGO_ID in doc and doc['id'] == doc[MONGO_ID]:
        del doc['id']


def close_db():
    global client
    if client:
        client.close()
        client = None


@needs_db
def create(collection, doc, db=GEO_DB):
    """
    Insert a single doc into collection.
    """
    print(f'{doc=}')
    ret = client[db][collection].insert_one(doc)
    return str(ret.inserted_id)


@needs_db
def read_one(collection, filt, db=GEO_DB):
    """
    Find with a filter and return on the first doc found.
    Return None if not found.
    """
    for doc in client[db][collection].find(filt):
        convert_mongo_id(doc)
        return doc


@needs_db
def read_many(collection: str, filt: dict, db=GEO_DB, no_id=True) -> list:
    """
    Returns all documents matching a filter.
    """
    results = []
    for doc in client[db][collection].find(filt):
        if no_id:
            doc.pop(MONGO_ID, None)
            doc.pop('id', None)  # Clean up legacy 'id' field
        else:
            convert_mongo_id(doc)
        results.append(doc)
    return results


@needs_db
def delete(collection: str, filt: dict, db=GEO_DB):
    """
    Find with a filter and return after deleting the first doc found.
    """
    print(f'{filt=}')
    del_result = client[db][collection].delete_one(filt)
    return del_result.deleted_count


@needs_db
def update(collection, filters, update_dict, db=GEO_DB):
    return client[db][collection].update_one(filters, {'$set': update_dict})


@needs_db
def read(collection, db=GEO_DB, no_id=True) -> list:
    """
    Returns a list from the db.
    """
    ret = []
    for doc in client[db][collection].find():
        if no_id:
            del doc[MONGO_ID]
            if 'id' in doc:  # Clean up legacy 'id' field
                del doc['id']
        else:
            convert_mongo_id(doc)
        ret.append(doc)
    return ret


def read_dict(collection, key, db=GEO_DB, no_id=True) -> dict:
    recs = read(collection, db=db, no_id=no_id)
    recs_as_dict = {}
    for rec in recs:
        recs_as_dict[rec[key]] = rec
    return recs_as_dict


@needs_db
def ensure_indexes(db=GEO_DB):
    """
    Create indexes for all collections to improve query performance.
    Safe to call multiple times - MongoDB ignores duplicate index creation.

    Primary keys:
    - countries: code (ISO country code)
    - states: state_code + country_code (composite)
    - cities: _id (MongoDB ObjectId, auto-indexed)
    """
    # Countries: code is the primary key
    client[db]['countries'].create_index('code', unique=True)

    # States: composite primary key on state_code + country_code
    client[db]['states'].create_index(
        [('state_code', pm.ASCENDING), ('country_code', pm.ASCENDING)],
        unique=True
    )
    client[db]['states'].create_index('country_code')  # for lookup by country

    # Cities: _id is auto-indexed by MongoDB
    # Additional index for state_code lookup
    client[db]['cities'].create_index('state_code')

    print('Database indexes created/verified.')


@needs_db
def exists(collection: str, filt: dict, db=GEO_DB) -> bool:
    """
    Check if a document matching the filter exists.
    More efficient than read_one when you only need existence check.
    """
    return client[db][collection].count_documents(filt, limit=1) > 0
