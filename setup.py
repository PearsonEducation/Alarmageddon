from setuptools import setup
setup(
        name = "Alarmageddon",
        description = "Automated testing and reporting",
        version = "0.1",
        author = "a field we should fill out",
        author_email = "email",
        url = "url",
        packages = ['alarmageddon',
                    "alarmageddon.publishing",
                    "alarmageddon.validations"],
        install_requires = ["fabric==1.8.0",
                            "pytest==2.4.2",
                            "Jinja2==2.7.2",
                            "requests==2.0.0",
                            "statsd==2.0.3",
                            "colorama==0.3.2",
                            "pika==0.9.13"]
        )
