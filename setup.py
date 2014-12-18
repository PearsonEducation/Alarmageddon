from setuptools import setup
setup(
        name = "Alarmageddon",
        description = "Automated testing and reporting",
        version = "1.0.0",
        author = "Tim Stewart, Scott Hellman",
        author_email = "timothy.stewart@pearson.com, scott.hellman@pearson.com",
        url = "https://github.com/PearsonEducation/Alarmageddon",
        license = "Apache2",
        classifiers=[
            "Development Status :: 5 - Production/Stable",
            "Programming Language :: Python :: 2 :: Only",
            "License :: OSI Approved :: Apache Software License"
            ],

        packages = ['alarmageddon',
                    "alarmageddon.publishing",
                    "alarmageddon.validations"],
        install_requires = ["fabric==1.8.0",
                            "Jinja2==2.7.2",
                            "requests==2.0.0",
                            "statsd==2.0.3",
                            "colorama==0.3.2",
                            "pycrypto==2.6.1",
                            "pika==0.9.13",
                            "pytest>=2.4.0",
                            "pytest-localserver==0.3.2"],
    )
