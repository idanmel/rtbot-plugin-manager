import threading
from unittest.mock import MagicMock

import pytest

from rtbot_plugin_manager.plugin_manager import PluginManager, PluginLoadingError
from rtbot_plugin_manager.tests.utils import OpenableNamedTemporaryFile


class PluginBase(MagicMock):
    def __init__(self):
        super(PluginBase, self).__init__()
        self.bar = 'bar'


@pytest.fixture
def pm():
    yield PluginManager()


@pytest.fixture
def pm_with_class_selector():
    yield PluginManager(class_selector=lambda cls: issubclass(cls, PluginBase) and not cls == PluginBase)


PLUGIN = """
class SimplePlugin:
    def foo(self):
        return 'simple plugin'
"""


PLUGIN_DIFFERENT_IMPLEMENTATION = """
class SimplePlugin:
    def foo(self):
        return 'different implementation'
"""


PLUGIN_WITH_CONSTRUCTOR_EXCEPTION = """
class SimplePlugin:
    def __init__(self):
        raise RuntimeException('Example plugin constructor exception')
"""


PLUGIN_WITH_CONSTRUCTOR_DESTRUCTOR = """
class SimplePlugin:
    def __init__(self):
        threadlocals = threading.local()
        threadlocals.constructor_called = True
    def __del__(self):   # DESIGN: the __del__ special method is problematic (https://docs.python.org/3.6/reference/datamodel.html#object.__del__), should we declare our own instead, e.g. on_destroy()
        threadlocals = threading.local()
        threadlocals.destructor_called = True
"""


PLUGIN_WITH_ASYNC_METHOD = """
class SimplePlugin(PluginBase):
    async def foo(self, val):
        self.bar(val)
"""


MULTIPLE_PLUGINS_MODULE = """
from rtbot_plugin_manager.tests.test_plugin_manager import PluginBase   # FIXME: is this the right import? And is that module available in the test environment?
class NotAPlugin:
    def __init__(self):
        raise Exception('I should not be instantiated!')
class PluginWithBaseClass(PluginBase):
    def foo(self):
        return 'plugin with base class'
class AlsoNotAPlugin:
    def __init__(self):
        raise Exception('I should not be instantiated!')
"""


PLUGIN_WITH_BASE_CLASS = """
from rtbot_plugin_manager.tests.test_plugin_manager import PluginBase   # FIXME: is this the right import? And is that module available in the test environment?
class PluginWithBaseClass(PluginBase):
    pass
"""


PLUGIN_WITH_SYNTAX_ERROR = """
class PluginWithSyntaxError:
    -
"""


def _assert_single_plugin(pm):
    assert len(pm.repository) == 1
    return list(pm.repository.values())[0]


def test_load_plugin(pm):
    # load plugin and assert its ID
    plugin_id = pm.load_plugin_from_string(PLUGIN)
    assert plugin_id

    # assert that there's exactly one plugin in the registry now
    plugin = _assert_single_plugin(pm)

    # check that the right class was loaded, instantiated and can be invoked
    assert plugin.__class__.__name__ == 'SimplePlugin'
    assert plugin.foo() == 'simple plugin'


def test_load_plugin_from_file(pm):
    # create temporary file to load plugin from
    with OpenableNamedTemporaryFile(mode='w+', suffix='.py', content=PLUGIN) as filename:
        # load plugin and assert its ID
        plugin_id = pm.load_plugin_from_file(filename)
        assert plugin_id

        # assert that there's exactly one plugin in the registry now
        plugin = _assert_single_plugin(pm)

        # check that the right class was loaded, instantiated and can be invoked
        assert plugin.__class__.__name__ == 'SimplePlugin'
        assert plugin.foo() == 'simple plugin'


def test_plugin_loading_by_class_selector(pm_with_class_selector):
    plugin_id = pm_with_class_selector.load_plugin_from_string(MULTIPLE_PLUGINS_MODULE)
    assert plugin_id

    plugin = pm_with_class_selector.repository[plugin_id]

    assert plugin.__class__.__name__ == 'PluginWithBaseClass'
    assert plugin.bar == 'bar'


def test_load_and_unload_plugin(pm):
    # load plugin
    plugin_id = pm.load_plugin_from_string(PLUGIN)
    plugin = _assert_single_plugin(pm)
    assert plugin.foo() == 'simple plugin'

    # unload plugin
    assert pm.unload_plugin(plugin_id)

    # check that the plugin repository is empty
    assert len(pm.repository) == 0


def test_plugins_have_unique_id(pm):
    # load and unload one plugin
    first_id = pm.load_plugin_from_string(PLUGIN)
    assert first_id
    assert pm.unload_plugin_from_string(first_id)

    # now load another plugin (not the same plugin with a different implementation)
    second_id = pm.load_plugin_from_string(PLUGIN_WITH_CONSTRUCTOR_DESTRUCTOR)
    assert second_id

    # assert that these two plugins were assigned unique IDs
    assert first_id != second_id


def test_plugin_id_is_independent_from_implementation(pm):
    # load and unload a plugin
    first_id = pm.load_plugin_from_string(PLUGIN)
    assert first_id
    assert pm.unload_plugin_from_string(first_id)

    # now load the same plugin with a different implementation
    second_id = pm.load_plugin_from_string(PLUGIN_DIFFERENT_IMPLEMENTATION)
    assert second_id

    # assert that these are considered the same plugin and were assigned the same ID
    assert first_id == second_id


def test_plugin_can_be_reloaded(pm):
    # load plugin and assert its ID
    plugin_id = pm.load_plugin_from_string(PLUGIN)
    assert plugin_id

    # assert that there's exactly one plugin in the registry now
    plugin = _assert_single_plugin(pm)

    # check that the right class was loaded, instantiated and can be invoked
    assert plugin.foo() == 'simple plugin'

    # now load a plugin with the same identification, and expect this to trigger a reload
    assert pm.load_plugin_from_string(PLUGIN_DIFFERENT_IMPLEMENTATION)
    assert plugin.foo() == 'different implementation'


def test_loading_plugin_calls_hook(pm):
    # TODO: anyone got a better idea than threadlocals (which seems rather unstable for a test case) to check whether these were invoked?

    # reset some thread-local variables
    threadlocals = threading.local()
    threadlocals.constructor_called = False
    threadlocals.destructor_called = False

    # load plugin
    plugin_id = pm.load_plugin_from_string(PLUGIN_WITH_CONSTRUCTOR_DESTRUCTOR)
    assert plugin_id

    # check that the constructor was called
    assert threadlocals.constructor_called

    # unload plugin
    pm.unload_plugin(plugin_id)
    assert threadlocals.destructor_called


def test_fire_plugin_events(pm):
    # load a plugin, which derives from MagicMock
    plugin_id = pm.load_plugin_from_string(PLUGIN_WITH_BASE_CLASS)

    # ask the plugin manager to invoke .foo('bar') on all plugins
    pm.fire_event(lambda plugin: plugin.foo('bar'))

    # check via the MagicMock that foo() has indeed been called once with argument 'bar'
    plugin = pm.repository[plugin_id]
    plugin.foo.assert_called_once_with('bar')


def test_fire_plugin_events_async(pm):
    # load a plugin, which derives from MagicMock
    plugin_id = pm.load_plugin_from_string(PLUGIN_WITH_ASYNC_METHOD)

    # ask the plugin manager to invoke .foo('bar') on all plugins
    async def call(plugin):
        await plugin.foo('bar')
    pm.fire_event_async(call)

    # check via the MagicMock that foo() has indeed been called once with argument 'bar'
    plugin = pm.repository[plugin_id]
    plugin.bar.assert_called_once_with('bar')


def test_load_syntactically_invalid_plugin(pm):
    with pytest.raises(PluginLoadingError) as exc:
        pm.load_plugin_from_string(PLUGIN_WITH_SYNTAX_ERROR)
    assert isinstance(exc.cause, SyntaxError)   # TODO: I don't actually know how to correctly access the cause... do I have to write __cause__ here!? https://docs.python.org/3/reference/simple_stmts.html#raise

    # make sure the plugin doesn't appear loaded
    assert 'PluginWithSyntaxError' not in pm.repository
    assert len(pm.repository) == 0


def test_load_plugin_with_error_during_initialization(pm):
    with pytest.raises(PluginLoadingError) as exc:
        pm.load_plugin_from_string(PLUGIN_WITH_CONSTRUCTOR_EXCEPTION)
    assert isinstance(exc.cause, RuntimeError)   # TODO: I don't actually know how to correctly access the cause... do I have to write __cause__ here!? https://docs.python.org/3/reference/simple_stmts.html#raise

    # make sure the plugin doesn't appear loaded
    assert 'SimplePlugin' not in pm.repository
    assert len(pm.repository) == 0


def test_reloading_plugin_unloads_original_instance(pm):
    # reset some thread-local variables
    threadlocals = threading.local()
    threadlocals.constructor_called = False
    threadlocals.destructor_called = False

    # load plugin
    assert pm.load_plugin_from_string(PLUGIN_WITH_CONSTRUCTOR_DESTRUCTOR)
    assert threadlocals.constructor_called

    # reloading plugin with a different implementation should unload the original instance
    pm.load_plugin_from_string(PLUGIN)
    assert threadlocals.destructor_called


def test_reload_plugin_with_newly_introduced_syntax_error(pm):
    # load a plugin
    plugin_id = pm.load_plugin_from_string(PLUGIN)
    assert plugin_id

    # now effectively reload the plugin after introducing a syntax error
    with pytest.raises(PluginLoadingError):
        pm.load_plugin_from_string(PLUGIN_WITH_CONSTRUCTOR_EXCEPTION)

    # this should result in the original plugin being unloaded
    assert 'SimplePlugin' not in pm.repository
    assert len(pm.repository) == 0
