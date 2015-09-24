import setuptools

setuptools.setup(
    name="tesora_horizon",
    version="1.0.0",
    packages=setuptools.find_packages(),
    include_package_data=True,
    package_data={'': ['**.html', ], },
)
