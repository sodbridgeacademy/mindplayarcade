
import os

import streamlit as st
from appwrite.client import Client
from appwrite.services.tables_db import TablesDB
from appwrite.services.account import Account


APPWRITE_DATABASE_ID = "mindplay_arcade"

def get_appwrite_client():
    """Create and configure the Appwrite client."""

    client = Client()

    client.set_endpoint(
        os.getenv("APPWRITE_ENDPOINT")
    )

    client.set_project(
        os.getenv("APPWRITE_PROJECT_ID")
    )

    client.set_key(
        os.getenv("APPWRITE_API_KEY")
    )

    return client


def get_database_service():
    """Return the Appwrite TablesDB service."""
    client = get_appwrite_client()
    return TablesDB(client)


def get_account_service():
    """Return the Appwrite account service."""

    client = get_appwrite_client()
    return Account(client)


def test_appwrite_connection():
    """Test the Appwrite connection and API key."""

    try:
        client = get_appwrite_client()
        databases = Databases(client)

        databases.list()

        return True, "Appwrite connection successful!"

    except Exception as error:
        return False, str(error)