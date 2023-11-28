from setuptools import setup, find_packages

setup(
    name='Daylio Markdown Export',
    version='1.0',
    packages=find_packages(),
    install_requires=[
        'click==8.1.7',
        'html2text==2020.1.16',
        'Jinja2==3.1.2',
        'MarkupSafe==2.1.3',
        'python-magic==0.4.27',
        'tqdm==4.66.1'
    ],
    entry_points={
        'console_scripts': [
            'daylio2markdown=daylio2markdown.__main__:main',
        ],
    },
)
