from setuptools import setup, find_packages

setup(
    name="quantum-dice-game",
    version="1.0.2",
    packages=find_packages(),  # <-- this ensures engines/ and pages/ are included
    include_package_data=True,
    install_requires=[
        # Add Qiskit, PyQt5, Watson dependencies here
    ],
    entry_points={
        "console_scripts": [
            "quantum-dice=quantum_dice_game.__main__:main",
        ],
    },
    python_requires=">=3.8",
)
