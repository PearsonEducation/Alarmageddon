from setuptools import setup
setup(
        name = "Alarmageddon",
        description = "Automated testing and reporting",
        version = "1.1.0",
        author = "Tim Stewart, Scott Hellman",
        author_email = "timothy.stewart@pearson.com, scott.hellman@pearson.com",
        url = "https://github.com/PearsonEducation/Alarmageddon/tarball/1.1.0",
        license = "Apache2",
        classifiers=[
            "Development Status :: 5 - Production/Stable",
            "Programming Language :: Python :: 2.7",
            "Programming Language :: Python :: 3.4"
            "License :: OSI Approved :: Apache Software License"
            ],

        packages = ['alarmageddon',
                    "alarmageddon.publishing",
                    "alarmageddon.validations"],
        install_requires = ["fabric==2.5.0",
                            "Jinja2==2.10.1",
                            "requests==2.22.0",
                            "statsd==2.0.3",
                            "colorama==0.3.2",
                            "pycrypto==2.6.1",
                            "six==1.13.0",
                            "pika==1.1.0",
                            "pytest==4.6.6"],
    )
