from setuptools import setup
setup(
        name = "Alarmageddon",
        description = "Automated testing and reporting",
        version = "1.0.5",
        author = "Tim Stewart, Scott Hellman",
        author_email = "timothy.stewart@pearson.com, scott.hellman@pearson.com",
        url = "https://github.com/PearsonEducation/Alarmageddon/tarball/1.0.5",
        license = "Apache2",
        classifiers=[
            "Development Status :: 5 - Production/Stable",
            "Programming Language :: Python :: 2 :: Only",
            "License :: OSI Approved :: Apache Software License"
            ],

        packages = ['alarmageddon',
                    "alarmageddon.publishing",
                    "alarmageddon.validations"],
        install_requires = ["fabric==2.5.0",
                            "Jinja2==2.7.2",
                            "requests==2.20.0",
                            "statsd==2.0.3",
                            "colorama==0.3.2",
                            "pycrypto==2.6.1",
                            "six==1.13.0",
                            "pika==0.9.13",
                            "pytest==4.6.6",
                            "pytest-localserver==0.5.0"],
    )
