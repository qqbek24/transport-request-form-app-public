"""
Utils package for Transport Request API

This package contains helper modules to keep the main fastapi_app.py clean and organized.

Modules:
- email_handler: Email parsing and sending functions
- excel_handler: Excel/SharePoint integration functions
- background_tasks: Background processing tasks
- json_handler: JSON backup file operations
"""

__all__ = [
    'email_handler',
    'excel_handler',
    'background_tasks',
    'json_handler'
]
