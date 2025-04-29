from setuptools import setup, find_packages

setup(
    name="kai-assistant",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "python-dotenv",
        "openai",
        "agno",
        "google-auth-oauthlib",
        "google-auth-httplib2",
        "google-api-python-client",
    ],
) 