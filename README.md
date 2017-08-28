# rtbot-plugin-manager
A plugin manager for RTBot

## Installation
pip install -e .

## Running tests
python setup.py test

## Terminology
* _plugin_: Loosely defined as a category of Python classes, of which we want to load, unload and reload a set of at runtime, the exact details of which aren't known during development.
* A plugin has an identification/name, which is based on its class name.
* Only a single plugin with a certain ID can exist at any time. If another plugin with the same ID is attempted to be loaded, it will be considered another implementation of the same plugin and it overwrites the previously registered plugin.
* A plugin is considered 'the same' as another plugin if they share the same selected class name.

## Open design questions:
* Should it be possible to have multiple plugins in a single module? (Currently: no)
