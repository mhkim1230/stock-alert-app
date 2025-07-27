from setuptools import setup, find_packages

setup(
    name="stock_alert_app",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'python-jose[cryptography]',
        'passlib[bcrypt]',
        'python-multipart',
        'apscheduler',
        'aiohttp',
        'beautifulsoup4',
        'python-dotenv',
        'colorlog'
    ]
) 